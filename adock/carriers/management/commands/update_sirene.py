import os
import subprocess
import sys
import tempfile
import zipfile
from glob import glob

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from adock.carriers import models as carriers_models


class Command(BaseCommand):
    help = "Update the Sirene DB with the downloaded data files."

    def handle(self, *args, **options):
        # Filename are composed of the year and day of year so they are sortable
        feeds = carriers_models.CarrierFeed.objects.filter(
            source="sirene", applied_at=None
        ).order_by("filename")
        for feed in feeds:
            with tempfile.TemporaryDirectory() as tmp_dirname:
                zip_filename = os.path.join(settings.DATAFILES_ROOT, feed.filename.name)
                with zipfile.ZipFile(zip_filename, "r") as zf:
                    zf.extractall(tmp_dirname)

                # List CSV files
                self.stdout.write("%s - %s" % (feed.title, feed.filename.name))
                for filename in glob(tmp_dirname + "/*.csv"):
                    # Call SQL script on it...
                    sed_ps = subprocess.Popen(
                        [
                            "sed",
                            "s:FILENAMEPLACEHOLDER:" + filename + ":g",
                            os.path.join(
                                settings.BASE_DIR, "scripts", "update-sirene.sql"
                            ),
                        ],
                        stdout=subprocess.PIPE,
                    )
                    psql_ps = subprocess.Popen(
                        ["psql", settings.DATABASES["default"]["NAME"]],
                        stdin=sed_ps.stdout,
                        stdout=subprocess.PIPE,
                    )
                    # Allow sed_ps to receive SIGPIPE if psql_ps exits.
                    sed_ps.stdout.close()
                    try:
                        # Until 6 millions of records for semester updates.
                        # The others are handled in 2 mn max.
                        rc = psql_ps.wait(timeout=60 * 60)
                    except subprocess.TimeoutExpired:
                        self.stderr.write(
                            self.style.ERROR("Timeout on running of '%s'" % filename)
                        )
                        sys.exit(1)

                    if rc == 0:
                        feed.applied_at = timezone.now()
                        feed.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                "Filename '%s' imported with success." % filename
                            )
                        )
                    else:
                        self.stderr.write(
                            self.style.ERROR(
                                "Failed to run 'update-sirene.sql' with the CSV file '%s'."
                                % filename
                            )
                        )
