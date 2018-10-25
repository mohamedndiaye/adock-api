import json

from django.test import TestCase

VALID_SIRET = "12345678912345"


class CarrierTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.detail_url = "TO_SET"

    def patch_carrier(self, data, status_code):
        response = self.client.patch(
            self.detail_url, json.dumps(data), "application/json"
        )
        self.assertEqual(response.status_code, status_code)
        return response.json()
