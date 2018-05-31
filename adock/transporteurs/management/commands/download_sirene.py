import re
import subprocess

import requests
from bs4 import BeautifulSoup

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from adock.transporteurs import models as transporteurs_models

SCRAPPER_URL = 'https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/'

# RE_STOCK_FILE = re.compile(r'sirene_\d{6}_L_M\.zip')
RE_DAILY_FILE = re.compile(r'sirene_\d{7}_E_Q\.zip')


class Command(BaseCommand):
    help = "Scrap the data.gouv.fr to get the list of available files and download them."

    def handle(self, *args, **options):
        r = requests.get(SCRAPPER_URL)
        soup = BeautifulSoup(r.content, 'html.parser')

        links = []
        # The script runs everyday but we allows almost 15 days w/o running
        for selected_link in soup.select('h4.list-group-item-heading > a')[:15]:
            link = {
                'title': selected_link.find('span').text,
                'url': selected_link.attrs['href']
            }
            if RE_DAILY_FILE.search(link['url']):
                links.append(link)

        # rsync them all
        for link in links:
            url = link['url']
            try:
                transporteurs_models.TransporteurFeed.objects.get(source='sirene', url=url)
            except ObjectDoesNotExist:
                subprocess.run(['wget', '-c', url, '-P', settings.DATAFILES_ROOT], check=True)
                transporteurs_models.TransporteurFeed.objects.create(
                    source='sirene',
                    title=link['title'],
                    url=url,
                    filename=url.split('/')[-1]
                )
