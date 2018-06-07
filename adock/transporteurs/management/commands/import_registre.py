from glob import glob
import os
import platform
import subprocess
import sys
import tempfile
import zipfile

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from adock.transporteurs import models as transporteurs_models


class Command(BaseCommand):
    help = "Import the latest downloaded CSV file of the registre."

    def handle(self, *args, **options):
        # Only the latest file is used (each file contains the full list)
        try:
            queryset = transporteurs_models.TransporteurFeed.objects.filter(
                source='registre', applied_at=None)
            feed = queryset.latest('downloaded_at')
        except transporteurs_models.TransporteurFeed.DoesNotExist:
            sys.exit(1)

        with tempfile.TemporaryDirectory() as tmp_dirname:
            zip_filename = os.path.join(settings.DATAFILES_ROOT, feed.filename)
            with zipfile.ZipFile(zip_filename, 'r') as zf:
                zf.extractall(tmp_dirname)

            # Check only one file in zip archive
            filenames = glob(tmp_dirname + '/*.csv')
            if len(filenames) > 1:
                self.stderr.write(
                    self.style.ERROR("The zip file '%s' contains several files (%s)." % (feed.filename, filenames))
                )
                sys.exit(1)

            # Get the uncompressed file
            filename = filenames[0]
            self.stdout.write(filename)

            # Exception for inferior OS (aka MacOS)
            system = platform.system()
            if system == 'Darwin':
                # You should have installed GNU sed
                sed_cmd = '/usr/local/bin/gsed'
            else:
                sed_cmd = '/bin/sed'

            # Remove the empty trailing line in the CSV file
            try:
                subprocess.check_call([sed_cmd, '-i', '$ d', filename])
            except subprocess.CalledProcessError as e:
                self.stderr.write(self.style.ERROR("%s") % e)
                self.stderr.write(self.style.ERROR("Unable to remove empty trailing line in registre '%s'." % filename))
                sys.exit(1)

            # Just replace the placeholder with too many lines of Python...
            sed_ps = subprocess.Popen(
                [
                    'sed',
                    's:FILENAMEPLACEHOLDER:' + filename + ':g',
                    os.path.join(settings.BASE_DIR, 'scripts', 'import-registre.sql')
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            try:
                output_data, stderr_data = sed_ps.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                sed_ps.kill()
                self.stderr.write(
                    self.style.ERROR("Timeout: sed of '%s'." % filename)
                )
                sys.exit(1)

            if stderr_data:
                self.stderr.write(
                    self.style.ERROR("Unable to 'sed' the file '%s'." % filename)
                )
                self.stderr.write(self.style.ERROR(stderr_data))
                sys.exit(1)

            # Call SQL script to import the CSV file
            psql_ps = subprocess.Popen(
                [
                    'psql',
                    settings.DATABASES['default']['NAME']
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            # Allow sed_ps to receive a SIGPIPE if p2 exits.
            sed_ps.stdout.close()
            try:
                # Max 60k records should be fast (1 mn max)
                output_data, stderr_data = psql_ps.communicate(input=output_data, timeout=60)
            except subprocess.TimeoutExpired:
                psql_ps.kill()
                self.stderr.write(
                    self.style.ERROR("Timeout: psql on file '%s'." % filename)
                )
                sys.exit(1)

            if stderr_data:
                self.stderr.write(
                    self.style.ERROR("Unable to 'psql' the file '%s' with 'import-registre.sql'." % filename)
                )
                self.stderr.write(self.style.ERROR(stderr_data))
                sys.exit(1)

            queryset.update(applied_at=timezone.now())
            self.stdout.write(
                self.style.SUCCESS("Filename '%s' imported with success." % filename)
            )
