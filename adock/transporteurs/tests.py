import json

from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import models
from . import factories

VALID_SIRET = '12345678912345'


class TransporteurTestCase(TestCase):
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

    def test_get_siren_nic(self):
        transporteur = factories.TransporteurFactory(siret=VALID_SIRET)
        self.assertEqual(transporteur.get_siren(), '123456789')
        self.assertEqual(transporteur.get_nic(), '12345')


class TransporteurSearchTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.search_url = reverse('transporteurs_recherche')

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
        response = self.client.get(self.search_url, {'q': VALID_SIRET})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 0)

    def test_one_result(self):
        factories.TransporteurFactory(siret=VALID_SIRET)
        response = self.client.get(self.search_url, {'q': VALID_SIRET})
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        transporteurs = data['results']
        self.assertEqual(len(transporteurs), 1)
        self.assertEqual(transporteurs[0]['siret'], VALID_SIRET)


class TransporteurDetailTestCase(TestCase):
    def setUp(self):
        self.transporteur = factories.TransporteurFactory(siret=VALID_SIRET)
        self.detail_url = reverse('transporteurs_detail',
            kwargs={'transporteur_siret': VALID_SIRET})

    def test_get(self):
        response = self.client.get(self.detail_url)
        data = json.loads(response.content)
        self.assertEqual(data['siret'], VALID_SIRET)
        self.assertEqual(data['raison_sociale'], self.transporteur.raison_sociale)
        self.assertEqual(data['completeness'], models.COMPLETENESS_PERCENT_MIN + 2 * models.EARNED_POINT_VALUE)

    def test_get_empty_phone(self):
        self.transporteur.telephone = ''
        self.transporteur.save()
        response = self.client.get(self.detail_url)
        data = json.loads(response.content)
        self.assertEqual(data['telephone'], '')

    def test_patch(self):
        NEW_PHONE = '+33240424546'
        NEW_EMAIL = 'foo@example.com'

        # Initial status
        self.assertNotEqual(self.transporteur.telephone, NEW_PHONE)
        self.assertNotEqual(self.transporteur.email, NEW_EMAIL)
        self.assertEqual(len(mail.outbox), 0)

        # Apply changes
        with self.settings(MANAGERS=(("Foo", 'foo@example.com'))):
            response = self.client.patch(self.detail_url, json.dumps({
                'telephone': NEW_PHONE,
                'email': NEW_EMAIL,
            }), 'application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Side effects
        self.assertEqual(data['telephone'], '02 40 42 45 46')
        self.assertEqual(data['email'], NEW_EMAIL)
        self.assertEqual(data['completeness'], 100)
        self.assertEqual(len(mail.outbox), 1)
        message = "[adock] Modification du transporteur %s" % self.transporteur.siret
        self.assertEqual(mail.outbox[0].subject, message)

    def test_invalid_patch_request(self):
        response = self.client.patch(self.detail_url, {'foo': 'foo'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Seules les requêtes PATCH en JSON sont prises en charge.')

    def test_invalid_phone(self):
        response = self.client.patch(self.detail_url, json.dumps({
            'telephone': '11223344556',
            'email': self.transporteur.email,
        }), 'application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        # Wrong French translation will be fixed in django-phonenumber-field > 2.0 (my patch)
        self.assertEqual(data['telephone'][0], "Entrez un numéro de téléphone valide.")

    def test_completeness(self):
        # The default factory sets telephone and email but they aren't validated
        self.assertEqual(self.transporteur.completeness, models.COMPLETENESS_PERCENT_MIN + 2 * models.EARNED_POINT_VALUE)

        # No telephone
        self.transporteur.telephone = ''
        self.transporteur.save()
        self.assertEqual(self.transporteur.completeness, models.COMPLETENESS_PERCENT_MIN + models.EARNED_POINT_VALUE)

        # No email
        self.transporteur.email = ''
        self.transporteur.save()
        self.assertEqual(self.transporteur.completeness, models.COMPLETENESS_PERCENT_MIN)

        # Updated email
        self.transporteur.email = 'foo@example.com'
        self.transporteur.validated_at = timezone.now()
        self.transporteur.save()
        self.assertEqual(self.transporteur.completeness, models.COMPLETENESS_PERCENT_MIN + 2 * models.EARNED_POINT_VALUE)

        # Fully defined 100%
        self.transporteur.telephone = '02 40 41 42 43'
        self.transporteur.validated_at = timezone.now()
        self.transporteur.save()
        self.assertEqual(self.transporteur.completeness, 100)
