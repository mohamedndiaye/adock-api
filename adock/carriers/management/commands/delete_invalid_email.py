import os
import re

from django.core.management.base import BaseCommand
from adock.carriers import models as carriers_models


class Command(BaseCommand):
    help = "Extract mail addresses from undelivered mails to remove them from DB."

    def add_arguments(self, parser):
        parser.add_argument("directory", nargs="?")

    def handle(self, *args, **options):
        directory = options["directory"]

        extracted_mails = []
        mail_regex = re.compile(r"^Original-Recipient: rfc822;(.*)$", re.MULTILINE)
        with os.scandir(directory) as it:
            for entry in it:
                if not entry.name.startswith(".") and entry.is_file():
                    try:
                        with open(entry.path) as f:
                            content = f.read()
                            mail_match = mail_regex.search(content)
                            if mail_match:
                                extracted_mails.append(mail_match.group(1))
                    except UnicodeDecodeError as e:
                        print(entry.path)
                        raise e

        self.stdout.write("Number of mails found: %d" % len(extracted_mails))
        self.stdout.write(
            "Number of matching carriers in DB: %d"
            % carriers_models.Carrier.objects.filter(email__in=extracted_mails).count()
        )
        carriers_models.Carrier.objects.filter(email__in=extracted_mails).update(
            email=""
        )
