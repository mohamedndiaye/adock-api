import json
import re

from django.conf import settings
from django.core import mail
from django.urls import reverse

from adock.accounts.test import AuthTestCase

from .. import factories, models


class SignCarrierCertificateTestCase(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.carrier = factories.CarrierFactory(with_editable=True)
        self.license_renewal_url = reverse(
            "carriers_license_renewal", kwargs={"carrier_siret": self.carrier.siret}
        )
        self.http_authorization = self.log_in()

    def get_token_from_body(self, body):
        url_search = re.search(
            r"%stransporteur/renouvellement/(?P<license_renewable_id>\d+)/confirmer/(?P<token>.+)/"
            % settings.HTTP_CLIENT_URL,
            body,
        )
        self.assertIsNotNone(url_search)
        return url_search.groupdict()["token"]

    def test_ask_license_renewal(self):
        response = self.client.post(
            self.license_renewal_url,
            {"lti_nombre": 0, "lc_nombre": 20},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.http_authorization,
        )
        self.assertEqual(response.status_code, 200)

        renewal = models.CarrierLicenseRenewal.objects.get()
        self.assertEqual(renewal.lti_nombre, 0)
        self.assertEqual(renewal.lc_nombre, 20)
        self.assertIsNotNone(renewal.created_at)
        self.assertIsNone(renewal.confirmed_at)

        # Extract token from mail
        token = self.get_token_from_body(mail.outbox[0].body)
        # Confirm
        confirm_url = reverse(
            "carriers_license_renewal_confirm",
            kwargs={"license_renewal_id": renewal.id, "token": token},
        )
        self.assertEqual(len(mail.outbox), 2)
        mail.outbox = []

        # Click on confirm link
        response = self.client.get(confirm_url)
        self.assertEqual(response.status_code, 200)

        renewal.refresh_from_db()
        self.assertIsNotNone(renewal.confirmed_at)

        # 1 - ask for new license to DREAL
        # 2 - log to managers
        self.assertEqual(len(mail.outbox), 2)
        message = "[A Dock] Demande de renouvellement de licence de %s n° SIREN %s" % (
            self.carrier.raison_sociale,
            self.carrier.get_siren(),
        )
        self.assertEqual(mail.outbox[0].subject, message)
        message = (
            "[A Dock] Demande de renouvellement de licence %s du transporteur %s confirmée"
            % (renewal.pk, self.carrier.siret)
        )
        self.assertEqual(mail.outbox[1].subject, message)

    def test_invalid_license_renewal(self):
        response = self.client.post(
            self.license_renewal_url,
            {"lti_nombre": "foo"},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.http_authorization,
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content.decode("utf-8"))
        self.assertIn("lti_nombre", data["errors"])
        self.assertNotIn("lc_nombre", data["errors"])

    def test_zero_license_renewal(self):
        response = self.client.post(
            self.license_renewal_url,
            {"lti_nombre": 0, "lc_nombre": 0},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.http_authorization,
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content.decode("utf-8"))
        self.assertIn("non_field_errors", data["errors"])
        self.assertEqual(
            data["errors"]["non_field_errors"][0],
            "Au moins, un nombre de license doit être renseigné.",
        )
