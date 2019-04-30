import re
from django.conf import settings
from django.core.management.base import BaseCommand

from adock.meta import models as meta_models


class Command(BaseCommand):
    help = "Compute stats from nginx log"

    def handle(self, *args, **options):
        # To count views on carrier profile
        regex_transporteurs = re.compile(
            "GET %stransporteurs/[0-9]" % settings.HTTP_SERVER_URL_ENDPOINT
        )
        regex_carriers = re.compile(
            "GET %scarriers/[0-9]" % settings.HTTP_SERVER_URL_ENDPOINT
        )

        # To count views on certificates
        regex_certificates = re.compile(
            "GET %scarriers/.*/certificate/" % settings.HTTP_SERVER_URL_ENDPOINT
        )

        # To count searches
        regex_recherches = re.compile(
            "GET %stransporteurs/recherche/" % settings.HTTP_SERVER_URL_ENDPOINT
        )
        regex_searches = re.compile(
            "GET %scarriers/search/" % settings.HTTP_SERVER_URL_ENDPOINT
        )

        stats = {}
        # No need for mmap on these small files for now...
        # The command should have access to the log file
        with open(settings.NGINX_ACCESS_LOG, "rt") as f:
            content = f.read()
            stats["carriers"] = len(regex_transporteurs.findall(content)) + len(
                regex_carriers.findall(content)
            )
            stats["certificates"] = len(regex_certificates.findall(content))
            stats["searches"] = len(regex_recherches.findall(content)) + len(
                regex_searches.findall(content)
            )

        meta_models.Meta.objects.update_or_create(
            name="nginx", defaults={"data": stats}
        )
