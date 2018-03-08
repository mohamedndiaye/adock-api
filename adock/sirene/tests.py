import json

from django.urls import reverse
from django.test import TestCase

from . import models as sirene_models

class SireneTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.search_url = reverse('sirene_search')

    def test_empty_search(self):
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertTrue('message' in data)
        self.assertEquals(data['message'], 'Empty query.')

    def test_one_invalid_param(self):
        response = self.client.get(self.search_url, {'q': '123'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertTrue('message' in data)
        self.assertEquals(data['message'], 'Required parameter not found.')

    def test_invalid_siren(self):
        response = self.client.get(self.search_url, {'siren': '123'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertTrue('message' in data)
        self.assertEquals(data['message'], 'Invalid SIREN/SIRET.')

    def test_empty_results_with_siren(self):
        response = self.client.get(self.search_url, {'siren': '123456789'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 0)

    def test_empty_results_with_siret(self):
        response = self.client.get(self.search_url, {'siren': '12345678912345'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 0)

    def test_one_result(self):
        sirene_models.Sirene.objects.create(
            siren='123456789',
            nic='12345',
            l1_normalisee='company'
        )
        response = self.client.get(self.search_url, {'siren': '12345678912345'})
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['results']), 1)
