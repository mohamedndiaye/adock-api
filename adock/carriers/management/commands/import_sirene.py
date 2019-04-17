from pathlib import Path
import gzip
import os
import shutil
import subprocess
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from adock.carriers import models as carriers_models


class Command(BaseCommand):
    help = "Import the latest downloaded CSV file of Sirene."

    def handle(self, *args, **options):
        # Only the latest file is used (each file contains the full list)
        try:
            queryset = carriers_models.CarrierFeed.objects.filter(
                source="sirene", applied_at=None
            )
            feed = queryset.latest("downloaded_at")
        except carriers_models.CarrierFeed.DoesNotExist:
            sys.exit(1)

        # The Python version of gunzip in command line...
        gzip_filename = os.path.join(settings.DATAFILES_ROOT, feed.filename.name)
        self.stdout.write("File to decompress: %s" % gzip_filename)
        with gzip.open(gzip_filename, "rb") as f_in:
            filename = str(Path(gzip_filename).with_suffix(""))
            with open(filename, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        self.stdout.write("psql import of '%s'..." % filename)
        # Call SQL script to import the CSV file
        psql_ps = subprocess.Popen(
            [
                "psql",
                settings.DATABASES["default"]["NAME"],
                "-f",
                os.path.join(settings.BASE_DIR, "scripts", "import-sirene.sql"),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            # Max 10 mn
            _, stderr_data = psql_ps.communicate(timeout=600)
        except subprocess.TimeoutExpired:
            psql_ps.kill()
            self.stderr.write(
                self.style.ERROR("Timeout: psql on file '%s'." % filename)
            )
            sys.exit(1)

        if stderr_data:
            self.stderr.write(
                self.style.ERROR(
                    "Unable to 'psql' the file '%s' with 'import-sirene.sql'."
                    % feed.filename.name
                )
            )
            self.stderr.write(self.style.ERROR(stderr_data))
            sys.exit(1)

        queryset.update(applied_at=timezone.now())
        self.stdout.write(
            self.style.SUCCESS("Geo Sirene '%s' imported with success." % filename)
        )
