from unittest import skipIf
import copy
import json

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

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


class SignCarrierCertificateTestCase(TestCase):
    def setUp(self):
        self.carrier = factories.CarrierFactory()
        self.url = reverse(
            "carriers_certificate", kwargs={"carrier_siret": self.carrier.siret}
        )

    def test_sign_certificate_workers(self):
        data = copy.copy(CERTIFICATE_DATA)
        data["kind"] = models.CERTIFICATE_WORKERS
        data["workers"] = CERTIFICATE_DATA_WORKERS
        response = self.client.post(
            self.url, json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        self.carrier.refresh_from_db()
        certificate = self.carrier.certificates.get()
        self.assertEqual(certificate.kind, models.CERTIFICATE_WORKERS)
        self.assertEqual(certificate.data["first_name"], data["first_name"])
        self.assertEqual(certificate.data["last_name"], data["last_name"])
        self.assertEqual(certificate.data["position"], data["position"])
        self.assertEqual(certificate.data["location"], data["location"])
        self.assertIn("workers", certificate.data)
        self.assertEqual(len(certificate.data["workers"]), 2)
        self.assertNotIn("kind", certificate.data)
        self.assertIsNotNone(certificate.created_at)

    def test_sign_certificate_no_WORKERS(self):
        data = copy.copy(CERTIFICATE_DATA)
        data["kind"] = models.CERTIFICATE_NO_WORKERS
        response = self.client.post(
            self.url, json.dumps(data), content_type="application/json"
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

    def test_sign_invalid_certificate_no_WORKERS(self):
        data = copy.copy(CERTIFICATE_DATA)
        # Empty field
        data["kind"] = models.CERTIFICATE_NO_WORKERS
        data["last_name"] = ""
        response = self.client.post(
            self.url, json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("last_name", data)


@skipIf(settings.USE_CIRCLECI, "Image not ready for CircleCI")
class GetCarrierCertificateTestCase(TestCase):
    def setUp(self):
        self.carrier = factories.CarrierFactory()
        self.url = reverse(
            "carriers_certificate", kwargs={"carrier_siret": self.carrier.siret}
        )

        def test_get_no_certificate(self):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 404)

    def test_get_certificate_workers(self):
        certificate = factories.CarrierCertificateFactory(
            carrier=self.carrier, kind=models.CERTIFICATE_WORKERS
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_get_certificate_no_workers(self):
        data = copy.copy(CERTIFICATE_DATA)
        data["workers"] = CERTIFICATE_DATA_WORKERS
        certificate = factories.CarrierCertificateFactory(
            carrier=self.carrier, kind=models.CERTIFICATE_NO_WORKERS, data=data
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
