#!/usr/bin/env python3
"""Python 3.6 code to run when the situation is hopeless."""

import ast
import datetime
import pprint
import re
from email.utils import parsedate_tz, mktime_tz

import psycopg2
import pytz
import requests

PP = pprint.PrettyPrinter(indent=4)

URL = "https://adock.beta.gouv.fr/api"
# URL = 'http://localhost:8000'


def extract_from_mbox(data):
    """Extract useful content from mbox"""
    cleaned_data = []
    subject_regex = re.compile(
        r"^Subject: \[adock\] Modification du transporteur (\d*)$.*?^"
        r"Date: (.*?)$.*?^Valeurs modifiées :$(.*?)^(From|---)",
        re.MULTILINE | re.DOTALL,
    )
    fields_regex = fields_regex = re.compile(
        r".*?(email|specialities|working_area_departemens|telephone"
        r"|description|working_area_departements|website)+ :(.*?)=>\s(.*?)$",
        re.MULTILINE | re.DOTALL,
    )
    for mail_body in subject_regex.findall(data):
        siret = mail_body[0]

        # print(f"SIRET: {siret}")
        timestamp = mktime_tz(parsedate_tz(mail_body[1]))
        date = datetime.datetime.fromtimestamp(timestamp)
        # print(f" Date: {date}")

        fields_extracted = fields_regex.findall(mail_body[2])
        # Don't expectchanges at the very same second!
        cleaned_data.append(
            {
                "siret": siret,
                "date": date,
                "json": {
                    f[0]: ast.literal_eval(f[2])
                    if f[2] != "" and f[2][0] == "["
                    else f[2]
                    for f in fields_extracted
                },
            }
        )

    cleaned_data_sorted_by_date = sorted(
        cleaned_data, key=lambda entry: entry["date"], reverse=True
    )
    return cleaned_data_sorted_by_date


def compact_changes(cleaned_data_by_date_desc):
    """
    Compact extracted changes to keep only the latest values of each field
    The latest change overwrites the others.
    """
    compact_data_by_siret = {}
    for entry in cleaned_data_by_date_desc:
        existing_entry = compact_data_by_siret.get(entry["siret"])
        if existing_entry:
            # Add not already present JSON fields (only latest are kept)
            existing_json_keys = existing_entry["json"].keys()
            for json_key in entry["json"].keys():
                if json_key not in existing_json_keys:
                    existing_entry["json"][json_key] = entry["json"][json_key]

            # Kept the older date (begin)
            if entry["date"] < existing_entry["date_begin"]:
                # Older date to use
                existing_entry["date_begin"] = entry["date"]
        else:
            # Add new date_begin field
            entry["date_begin"] = entry["date"]
            # Create new entry
            compact_data_by_siret[entry["siret"]] = entry

    return compact_data_by_siret


def post_request(compact_data_by_siret):
    """PATCH requests againt our A Dock server API to edit carriers"""
    for siret in compact_data_by_siret:
        print(siret)
        PP.pprint(compact_data_by_siret[siret]["json"])
        request = requests.patch(
            f"{URL}/carriers/{siret}/", json=compact_data_by_siret[siret]["json"]
        )
        if request.status_code == 400:
            print(f"ERROR {request.content}")


def update_db_validated_at(compact_data_by_siret, start):
    """Restore the date of the validation on DB rows"""
    connection = psycopg2.connect("dbname=adock")
    cursor = connection.cursor()

    with open("adock-validated-at.sql", "w") as sql_output:
        for data in compact_data_by_siret.values():
            # set_fields = ", ".join(f"{k} = %s" for k in data['json'].keys())
            query = f"""
                UPDATE carrier
                SET validated_at = %s
                WHERE siret = %s AND validated_at > %s
            """
            cursor.execute(query, [data["date_begin"], data["siret"], start])
            sql_output.write(cursor.query.decode("utf-8") + ";")
            # query = f"""
            #     UPDATE carrier_log
            #        SET created_at = %s
            #     WHERE carrier_id = %s
            # """
            # cursor.execute(query, [data['date_begin'], data['siret']])

    cursor.execute("COMMIT")
    cursor.close()
    connection.close()


def main():
    """Call all the functions to extract and post requests"""
    with open("Client-MTES-A Dock.mbox", encoding="utf-8") as mbox_file:
        data = mbox_file.read()

    cleaned_data_by_date_desc = extract_from_mbox(data)
    compact_data_by_siret = compact_changes(cleaned_data_by_date_desc)
    start = datetime.datetime.now(pytz.timezone("Europe/Paris"))
    post_request(compact_data_by_siret)
    update_db_validated_at(compact_data_by_siret, start)


if __name__ == "__main__":
    main()
