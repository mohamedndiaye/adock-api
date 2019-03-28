from unittest import skipIf
import copy
import json
import re

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from adock.accounts.test import AuthTestCase

from .. import factories, models


CERTIFICATE_DATA = {
    "first_name": "Jérôme",
    "last_name": "Martin",
    "position": "Gérant",
    "location": "Corps-Nuds",
}

CERTIFICATE_DATA_WORKERS = [
    {
        "name": "Amporn Hyapha",
        "date": "2018-07-23",
        "nationality": "taïwanaise",
        "work_permit": "48304 TA",
    },
    {
        "name": "Bolingo Bafodé",
        "date": "2018-12-23",
        "nationality": "bangalais",
        "work_permit": "AAZ-4546-6767",
    },
]


class SignCarrierCertificateTestCase(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.carrier = factories.CarrierFactory(with_editable=True)
        self.detail_url = reverse(
            "carriers_certificate_detail", kwargs={"carrier_siret": self.carrier.siret}
        )
        self.http_authorization = self.log_in()

    def get_token_from_body(self, body):
        url_search = re.search(
            r"%stransporteur/attestation/(?P<certificate_id>\d+)/confirmer/(?P<token>.+)/"
            % settings.HTTP_CLIENT_URL,
            body,
        )
        self.assertIsNotNone(url_search)
        return url_search.groupdict()["token"]

    def test_sign_certificate_workers(self):
        data = copy.copy(CERTIFICATE_DATA)
        data["kind"] = models.CERTIFICATE_WORKERS
        data["workers"] = CERTIFICATE_DATA_WORKERS
        response = self.client.post(
            self.detail_url,
            data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.http_authorization,
        )
        self.assertEqual(response.status_code, 200)

        self.carrier.refresh_from_db()
        # Not confirmed yet
        self.assertIsNone(self.carrier.get_latest_certificate())
        certificate = models.CarrierCertificate.objects.get()
        self.assertEqual(certificate.kind, models.CERTIFICATE_WORKERS)
        self.assertEqual(certificate.data["first_name"], data["first_name"])
        self.assertEqual(certificate.data["last_name"], data["last_name"])
        self.assertEqual(certificate.data["position"], data["position"])
        self.assertEqual(certificate.data["location"], data["location"])
        self.assertIn("workers", certificate.data)
        self.assertEqual(len(certificate.data["workers"]), 2)
        self.assertNotIn("kind", certificate.data)
        self.assertIsNotNone(certificate.created_at)
        self.assertIsNone(certificate.confirmed_at)

        # Extract token from mail
        token = self.get_token_from_body(mail.outbox[0].body)
        # Confirm
        confirm_url = reverse(
            "carriers_certificate_confirm",
            kwargs={"certificate_id": certificate.id, "token": token},
        )
        self.assertEqual(len(mail.outbox), 2)
        mail.outbox = []

        response = self.client.get(confirm_url)
        self.assertEqual(response.status_code, 200)

        latest_certificate = self.carrier.get_latest_certificate()
        self.assertEqual(certificate, latest_certificate)
        self.assertIsNotNone(latest_certificate.confirmed_at)

        message = "[A Dock] L'attestation %s du transporteur %s a été confirmée." % (
            certificate.pk,
            self.carrier.siret,
        )
        self.assertEqual(mail.outbox[0].subject, message)

    def test_sign_certificate_no_workers(self):
        data = copy.copy(CERTIFICATE_DATA)
        data["kind"] = models.CERTIFICATE_NO_WORKERS
        response = self.client.post(
            self.detail_url,
            data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.http_authorization,
        )
        self.assertEqual(response.status_code, 200)

        self.carrier.refresh_from_db()
        certificate = self.carrier.certificates.get()
        self.assertEqual(certificate.kind, models.CERTIFICATE_NO_WORKERS)
        self.assertEqual(certificate.data["first_name"], data["first_name"])
        self.assertEqual(certificate.data["last_name"], data["last_name"])
        self.assertEqual(certificate.data["position"], data["position"])
        self.assertEqual(certificate.data["location"], data["location"])
        self.assertNotIn("workers", certificate.data)
        self.assertIsNotNone(certificate.created_at)

    def test_sign_invalid_certificate_no_workers(self):
        data = copy.copy(CERTIFICATE_DATA)
        # Empty field
        data["kind"] = models.CERTIFICATE_NO_WORKERS
        data["last_name"] = ""
        response = self.client.post(
            self.detail_url,
            data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.http_authorization,
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content.decode("utf-8"))
        self.assertIn("last_name", data["errors"])

    def test_sign_with_unconfirmed_carrier(self):
        self.carrier.editable.email = ""
        self.carrier.editable.save()

        data = copy.copy(CERTIFICATE_DATA)
        data["kind"] = models.CERTIFICATE_NO_WORKERS
        response = self.client.post(
            self.detail_url,
            data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.http_authorization,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"],
            "Vous devez d'abord confirmer la fiche transporteur avant de générer l'attestation.",
        )


@skipIf(settings.USE_CIRCLECI, "Image not ready for CircleCI")
class GetCarrierCertificateTestCase(TestCase):
    def setUp(self):
        self.carrier = factories.CarrierFactory()
        self.url = reverse(
            "carriers_certificate_detail", kwargs={"carrier_siret": self.carrier.siret}
        )

    def test_get_no_certificate(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_get_certificate_workers(self):
        factories.CarrierCertificateFactory(
            carrier=self.carrier, kind=models.CERTIFICATE_WORKERS
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_get_certificate_no_workers(self):
        data = copy.copy(CERTIFICATE_DATA)
        data["workers"] = CERTIFICATE_DATA_WORKERS
        factories.CarrierCertificateFactory(
            carrier=self.carrier, kind=models.CERTIFICATE_NO_WORKERS, data=data
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
