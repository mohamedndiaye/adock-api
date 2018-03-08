import json

from django.urls import reverse
from django.test import TestCase

class SireneTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.search_url = reverse('sirene_search')

    def test_empty_search(self):
        response = self.client.get(self.search_url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('message' in data)
        self.assertEquals(data['message'], 'Empty query.')

    def test_one_invalid_param(self):
        response = self.client.get(self.search_url, {'q': '123'})
        data = json.loads(response.content)
        self.assertTrue('message' in data)
        self.assertEquals(data['message'], 'Required parameter not found.')
        self.assertEqual(response.status_code, 400)
