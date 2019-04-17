from unittest import skipIf
import datetime
import pytz
import random

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from adock.carriers import factories as carriers_factories
from adock.accounts.test import AuthTestCase


class StatsTestCase(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("stats")

    def test_stats(self):
        STATS_NB_MONTHS = 6

        # One carrier not confirmed
        carriers_factories.CarrierFactory(with_editable=True)

        # 3 carriers confirmed over the n previous month
        now = timezone.now()
        paris_tz = pytz.timezone("Europe/Paris")
        first_day_of_current_month = datetime.datetime(
            year=now.year, month=now.month, day=1
        )
        # Approx first day 6 month ago (no datedelta dependency)
        start = paris_tz.localize(
            first_day_of_current_month - datetime.timedelta(days=STATS_NB_MONTHS * 30)
        )
        for _ in range(3):
            confirmed_at = start + datetime.timedelta(
                days=random.randint(1, STATS_NB_MONTHS * 30)
            )
            carriers_factories.CarrierFactory(
                with_editable={"confirmed_at": confirmed_at}
            )

        # One carrier validated outside of the range of stats
        carriers_factories.CarrierFactory(
            with_editable={
                "confirmed_at": timezone.now()
                - datetime.timedelta(days=STATS_NB_MONTHS * 31)
            }
        )

        http_authorization = self.log_in()
        response = self.client.get(
            self.url,
            content_type="application/json",
            HTTP_AUTHORIZATION=http_authorization,
        )
        self.assertEqual(response.status_code, 200)
        stats = response.json()

        # Total (outside last n months included)
        self.assertEqual(stats["modified_carriers"], 4)

        # 6 months
        modified_carriers_per_month = stats["modified_carriers_per_month"]
        self.assertEqual(len(modified_carriers_per_month), STATS_NB_MONTHS)
        self.assertEqual(
            sum([item["count"] for item in modified_carriers_per_month]), 3
        )
