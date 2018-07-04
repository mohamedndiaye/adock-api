import json

from django.test import TestCase

VALID_SIRET = '12345678912345'


class TransporteurTestCase(TestCase):

    def patch_transporteur(self, data, status_code):
        response = self.client.patch(self.detail_url, json.dumps(data), 'application/json')
        self.assertEqual(response.status_code, status_code)
        return response.json()
