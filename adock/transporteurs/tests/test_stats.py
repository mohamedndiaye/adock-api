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
        validated_date = (
            timezone.now() - datetime.timedelta(days=random.randint(1, nb_months - 1) * 31)
        ).replace(day=1)
        factories.TransporteurFactory(validated_at=validated_date)

        factories.TransporteurFactory(email_confirmed_at=validated_date)

        url = reverse('transporteurs_stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        stats = response.json()

        validated_transporteurs = stats['validated_transporteurs']
        # 12 months
        self.assertEqual(len(validated_transporteurs), nb_months)
        self.assertEqual(sum([item['count'] for item in validated_transporteurs]), 1)
        validated_date_str = str(validated_date.date())

        # Filter on month of the factory (one validation)
        filtered_months = list(filter(lambda item: item['month'] == validated_date_str, validated_transporteurs))
        self.assertEqual(filtered_months[0]['count'], 1)

        self.assertEqual(stats['confirmed_transporteurs'], 1)
