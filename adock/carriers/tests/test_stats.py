import datetime
import random

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .. import factories


class CarrierStatsTestCase(TestCase):
    def test_stats(self):
        STATS_NB_MONTHS = 6

        # One carrier not validated
        factories.CarrierFactory(validated_at=None)

        # First day in one of 10 previous months
        validated_date = (
            timezone.now()
            - datetime.timedelta(days=random.randint(1, STATS_NB_MONTHS - 1) * 31)
        ).replace(day=1)
        factories.CarrierFactory(validated_at=validated_date)

        # One carrier validated outside of the range of stats
        factories.CarrierFactory(
            validated_at=timezone.now() - datetime.timedelta(days=STATS_NB_MONTHS * 31)
        )

        # 2 locked sheets
        factories.CarrierFactory.create_batch(3, email_confirmed_at=validated_date)

        url = reverse("carriers_stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        stats = response.json()

        self.assertEqual(stats["locked_carriers"], 3)
        self.assertEqual(stats["validated_carriers"], 2)

        validated_carriers = stats["validated_carriers_per_month"]
        # 6 months
        self.assertEqual(len(validated_carriers), STATS_NB_MONTHS)
        self.assertEqual(sum([item["count"] for item in validated_carriers]), 1)
        validated_date_str = str(validated_date.date())

        # Filter on month of the factory (one validation)
        filtered_months = list(
            filter(lambda item: item["month"] == validated_date_str, validated_carriers)
        )
        self.assertEqual(filtered_months[0]["count"], 1)