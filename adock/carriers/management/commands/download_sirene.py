import os
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand

from adock.carriers import models as carriers_models

# The file is updated once a month
SIRENE_URL = "http://data.cquest.org/geo_sirene/v2019/last/"


class Command(BaseCommand):
    help = "Download latest geo CSV of Sirene."

    def handle(self, *args, **options):
        filename = "StockEtablissement_utf8_geo.csv.gz"
        full_filename = os.path.join(settings.DATAFILES_ROOT, filename)

        if os.path.isfile(full_filename):
            os.remove(full_filename)

        url = SIRENE_URL + filename
        subprocess.run(["wget", "-c", url, "-O", full_filename], check=True)
        carriers_models.CarrierFeed.objects.create(
            source="sirene", title=filename, url=url, filename=filename
        )
