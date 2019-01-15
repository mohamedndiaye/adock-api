import json

from django.test import TestCase
from django.urls import reverse

from .. import factories, models


class CarrierCertificateTestCase(TestCase):
    def test_sign_certificate_no_foreigners(self):
        carrier = factories.CarrierFactory()
        url = reverse(
            "carriers_certificate_no_foreigners",
            kwargs={"carrier_siret": carrier.siret},
        )

        data = {
            "first_name": "Jérôme",
            "last_name": "Martin",
            "position": "Gérant",
            "location": "Corps-Nuds",
        }
        response = self.client.post(
            url, json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        carrier.refresh_from_db()
        certificate = carrier.certificates.get()
        self.assertEqual(certificate.kind, models.CERTIFICATE_NO_FOREIGNERS)
        self.assertEqual(certificate.data["first_name"], data["first_name"])
        self.assertEqual(certificate.data["last_name"], data["last_name"])
        self.assertEqual(certificate.data["position"], data["position"])
        self.assertEqual(certificate.data["location"], data["location"])
        self.assertIsNotNone(certificate.created_at)

    def test_get_certificate_no_foreigners(self):
        certificate = factories.CarrierCertificateFactory()
        url = reverse(
            "carriers_certificate_no_foreigners",
            kwargs={"carrier_siret": certificate.carrier.siret},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
