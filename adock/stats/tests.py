from unittest import skipIf
import datetime
import random

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from adock.carriers import factories as carriers_factories
from adock.accounts.test import AuthTestCaseBase
from adock.accounts import factories as accounts_factories


class StatsTestCase(AuthTestCaseBase):
    def setUp(self):
        super().setUp()
        self.url = reverse("stats")

    @skipIf(settings.AUTHENTICATION_DISABLED, "Authentication is disabled")
    def test_no_logged(self):
        response = self.client.get(self.url, content_type="application/json")
        self.assertEqual(response.status_code, 401)

    @skipIf(settings.AUTHENTICATION_DISABLED, "Authentication is disabled")
    def test_staff_only(self):
        user = accounts_factories.UserFactory(
            email="courriel@example.com", is_staff=False
        )
        user.set_password("password")
        user.save()

        http_authorization = self.log_in(user.email, "password")
        response = self.client.get(
            self.url,
            content_type="application/json",
            HTTP_AUTHORIZATION=http_authorization,
        )
        self.assertEqual(response.status_code, 403)

    def test_stats(self):
        STATS_NB_MONTHS = 6

        # One carrier not confirmed
        carriers_factories.CarrierFactory(with_editable=True)

        for _ in range(3):
            confirmed_at = (
                timezone.now()
                - datetime.timedelta(days=random.randint(1, STATS_NB_MONTHS - 1) * 31)
            ).replace(day=1)
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

        self.assertEqual(stats["modified_carriers"], 4)

        # 6 months
        modified_carriers_per_month = stats["modified_carriers_per_month"]
        self.assertEqual(len(modified_carriers_per_month), STATS_NB_MONTHS)
        self.assertEqual(
            sum([item["count"] for item in modified_carriers_per_month]), 3
        )
