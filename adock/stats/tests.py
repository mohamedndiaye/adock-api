import datetime
import random

import datedelta
from django.urls import reverse
from django.utils import timezone
import pytz

from adock.carriers import factories as carriers_factories
from adock.carriers import models as carriers_models
from adock.accounts.test import AuthTestCase


class StatsTestCase(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("stats")

    def test_stats(self):
        NB_MONTHS = 6

        # One carrier not confirmed
        carriers_factories.CarrierFactory(with_editable=True)

        # 3 carriers confirmed over the n previous month
        now = timezone.now()
        paris_tz = pytz.timezone("Europe/Paris")
        first_day_of_current_month = paris_tz.localize(
            datetime.datetime(year=now.year, month=now.month, day=1)
        )
        # First day of the period
        start = first_day_of_current_month - datedelta.datedelta(months=NB_MONTHS - 1)
        for _ in range(3):
            # Use 30 days by month to stay within the period
            confirmed_at = start + datetime.timedelta(
                days=random.randint(1, NB_MONTHS * 30)
            )
            carriers_factories.CarrierFactory(
                with_editable={"confirmed_at": confirmed_at}
            )

        # One carrier validated outside of the range of stats
        carriers_factories.CarrierFactory(
            with_editable={"confirmed_at": start - datetime.timedelta(days=42)}
        )

        # Two certificates with only one confirmed
        carriers = carriers_models.Carrier.objects.all()[:2]
        carriers_factories.CarrierCertificateFactory(
            carrier=carriers[0], confirmed_at=None
        )
        carriers_factories.CarrierCertificateFactory(carrier=carriers[1])

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
        self.assertEqual(stats["certificates"], 1)

        # 6 months
        modified_carriers_per_month = stats["modified_carriers_per_month"]
        self.assertEqual(len(modified_carriers_per_month), NB_MONTHS)
        self.assertEqual(
            sum([item["count"] for item in modified_carriers_per_month]), 3
        )
