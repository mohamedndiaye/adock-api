import os
import subprocess
import tempfile
import zipfile

from django.conf import settings
from django.core.management.base import BaseCommand

from adock.transporteurs import models as transporteurs_models


class Command(BaseCommand):
    help = "Update the Sirene DB with the downloaded data files."

    def handle(self, *args, **options):
        scrapers = transporteurs_models.TransporteurScraper.objects.filter(is_applied=False)
        for scraper in scrapers:
            with tempfile.TemporaryDirectory() as tmp_dirname:
                zip_filename = os.path.join(settings.DATAFILES_ROOT, scraper.url.split('/')[-1])
                with zipfile.ZipFile(zip_filename, 'r') as zf:
                    zf.extractall(tmp_dirname)

                # List CSV file
                for root, dirs, files in os.walk(tmp_dirname):
                    fullname = os.path.join(root, files[0])
                    print(fullname)
                    # Call SQL script on it...
                    sed_ps = subprocess.Popen(
                        [
                            'sed',
                            's:FILENAMEPLACEHOLDER:' + fullname + ':g',
                            os.path.join(settings.BASE_DIR, 'scripts', 'update-sirene.sql')
                        ],
                        stdout=subprocess.PIPE
                    )
                    psql_ps = subprocess.Popen(
                        [
                            'psql',
                            settings.DATABASES['default']['NAME']
                        ],
                        stdin=sed_ps.stdin,
                        stdout=subprocess.PIPE
                    )
                    sed_ps.stdout.close()
                    print(psql_ps.communicate()[0])
