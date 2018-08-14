import datetime
import random

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .. import factories


class TransporteurStatsTestCase(TestCase):

    def test_stats(self):
        nb_months = 6
        factories.TransporteurFactory(validated_at=None)

        # First day in one of 10 previous months
        validated_date = (timezone.now() - datetime.timedelta(days=random.randint(1, nb_months - 1) * 31)).replace(day=1)
        factories.TransporteurFactory(validated_at=validated_date)

        url = reverse('transporteurs_stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        stats = response.json()['validated_transporteurs']
        # 12 months
        self.assertEqual(len(stats), nb_months)
        self.assertEqual(sum([stat['count'] for stat in stats]), 1)
        validated_date_str = str(validated_date.date())

        # Filter on month of the factory (one validation)
        filtered_months = list(filter(lambda stat: stat['month'] == validated_date_str, stats))
        self.assertEqual(filtered_months[0]['count'], 1)
