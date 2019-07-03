from django.test import TestCase

VALID_SIRET = "12345678912345"
VALID_SIRET_WITH_SPACES = "123 456 789 12345"


class CarrierTestCaseMixin(TestCase):
    def post_carrier(self, data, status_code):
        response = self.client.post(
            self.detail_url, data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status_code)
        return response.json()

    def post_carrier_logged(self, data, status_code):
        response = self.client.post(
            self.detail_url,
            data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.http_authorization,
        )
        self.assertEqual(response.status_code, status_code)
        return response.json()
