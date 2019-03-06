from django.test import TestCase

VALID_SIRET = "12345678912345"


class CarrierTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.detail_url = "TO_SET"

    def post_carrier(self, data, status_code):
        response = self.client.post(
            self.detail_url, data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status_code)
        return response.json()
