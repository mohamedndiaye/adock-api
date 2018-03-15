import json

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from . import factories

class TransporteurTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.search_url = reverse('transporteurs_recherche')

    def test_validators_too_short(self):
        transporteur = factories.TransporteurFactory(siret='1234567891234')
        with self.assertRaises(ValidationError) as cm:
            transporteur.full_clean()

        messages = cm.exception.message_dict
        self.assertEqual(messages['siret'][0], "1234567891234 n'est pas un numéro SIRET valide")

    def test_validators_not_digit(self):
        transporteur = factories.TransporteurFactory(siret='1A345678912345')

        with self.assertRaises(ValidationError):
            transporteur.full_clean()

    def test_vat_number(self):
        transporteur = factories.TransporteurFactory(siret='75001709700015')
        self.assertEqual(transporteur.get_vat_number(), 'FR18750017097')

    def test_get_siren_nic(self):
        transporteur = factories.TransporteurFactory(siret='12345678912345')
        self.assertEqual(transporteur.get_siren(), '123456789')
        self.assertEqual(transporteur.get_nic(), '12345')

    def test_empty_search(self):
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertTrue('message' in data)
        self.assertEquals(data['message'], "La requête est vide.")

    def test_one_invalid_param(self):
        response = self.client.get(self.search_url, {'q': '123'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertTrue('message' in data)
        self.assertEquals(data['message'], "Le paramètre de recherche n'est pas valide.")

    def test_invalid_siren(self):
        response = self.client.get(self.search_url, {'q': '123'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertTrue('message' in data)
        self.assertEquals(data['message'], "Le paramètre de recherche n'est pas valide.")

    def test_empty_results_with_siren(self):
        response = self.client.get(self.search_url, {'q': '123456789'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 0)

    def test_empty_results_with_siret(self):
        response = self.client.get(self.search_url, {'q': '12345678912345'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 0)

    def test_one_result(self):
        siret = '12345678912345'
        factories.TransporteurFactory(siret=siret)
        response = self.client.get(self.search_url, {'q': siret})
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        transporteurs = data['results']
        self.assertEqual(len(transporteurs), 1)
        self.assertEqual(transporteurs[0]['siret'], siret)
