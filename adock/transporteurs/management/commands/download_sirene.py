import datetime
import re
import subprocess

import requests
from bs4 import BeautifulSoup

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from adock.transporteurs import models as transporteurs_models

FILES_URL = "http://files.data.gouv.fr/sirene/"

# RE_STOCK_FILE = re.compile(r'sirene_\d{6}_L_M\.zip')
RE_DAILY_FILE = re.compile(r"sirene_(\d{4})(\d{3})_E_Q\.zip")


class Command(BaseCommand):
    help = (
        "Scrap files.data.gouv.fr to get the list of available files and download them."
    )

    def handle(self, *args, **options):
        r = requests.get(FILES_URL)
        soup = BeautifulSoup(r.content, "html.parser")

        zip_files = []
        # The script runs everyday but we allow about one week w/o running
        for selected_link in soup.select(
            "tr.item.type-application.type-zip > td.colname > a"
        )[-7:]:
            filename = selected_link.attrs["href"]
            zip_search = RE_DAILY_FILE.search(filename)
            if zip_search:
                year = int(zip_search.groups()[0])
                day_of_year = int(zip_search.groups()[1])
                zip_date = datetime.datetime(
                    year=year, month=1, day=1
                ) + datetime.timedelta(days=day_of_year - 1)
                title = "Sirene : mise à jour quotidienne du %s" % zip_date.strftime(
                    "%d/%m/%Y"
                )
                zip_files.append({"title": title, "filename": filename})

        # rsync them all
        for zip_file in zip_files:
            url = FILES_URL + zip_file["filename"]
            try:
                transporteurs_models.TransporteurFeed.objects.get(
                    source="sirene", url=url
                )
            except ObjectDoesNotExist:
                subprocess.run(
                    ["wget", "-c", url, "-P", settings.DATAFILES_ROOT], check=True
                )
                transporteurs_models.TransporteurFeed.objects.create(
                    source="sirene",
                    title=zip_file["title"],
                    url=url,
                    filename=zip_file["filename"],
                )
