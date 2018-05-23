from glob import glob
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

                # List CSV files
                for filename in glob(tmp_dirname + '/*.csv'):
                    print(filename)
                    # Call SQL script on it...
                    sed_ps = subprocess.Popen(
                        [
                            'sed',
                            's:FILENAMEPLACEHOLDER:' + filename + ':g',
                            os.path.join(settings.BASE_DIR, 'scripts', 'update-sirene.sql')
                        ],
                        stdout=subprocess.PIPE,
                    )
                    psql_ps = subprocess.Popen(
                        [
                            'psql',
                            settings.DATABASES['default']['NAME']
                        ],
                        stdin=sed_ps.stdout,
                        stdout=subprocess.PIPE
                    )
                    # Allow sed_ps to receive SIGPIPE if psql_ps exits.
                    sed_ps.stdout.close()
                    try:
                        # Until 6 millions of records (10 mn max)
                        rc = psql_ps.wait(timeout=10 * 60)
                    except subprocess.TimeoutExpired:
                        self.stderr.write(
                            self.style.ERROR("Timeout on running of '%s'" % filename))

                    if rc == 0:
                        scraper.is_applied = True
                        scraper.save()
                        self.stdout.write(
                            self.style.SUCCESS("Filename '%s' imported with success." % filename))
                    else:
                        self.stderr.write(
                            self.style.ERROR("Failed to run the SQL script 'update-sirene.sql' with the CSV file '%s'." % filename))
