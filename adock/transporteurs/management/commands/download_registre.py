import os
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand

from adock.transporteurs import models as transporteurs_models

REGISTRE_URL = 'http://www2.transports.equipement.gouv.fr/registres/marchandises/SITR_Liste_des_entreprises_Marchandises_sortie_CSV.zip'


class Command(BaseCommand):
    help = "Download the latest registre DB."

    def handle(self, *args, **options):
        filename = 'registre.zip'
        full_filename = os.path.join(settings.DATAFILES_ROOT, filename)

        if os.path.isfile(full_filename):
            os.remove(full_filename)

        subprocess.run(['wget', '-c', REGISTRE_URL, '-O', full_filename], check=True)
        transporteurs_models.TransporteurFeed.objects.create(
            source='registre',
            title='SITR_Liste_des_entreprises_Marchandises_sortie_CSV',
            url=REGISTRE_URL,
            filename=filename
        )
