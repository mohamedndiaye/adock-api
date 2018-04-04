import json

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .. import models
from .. import factories
from . import test


class TransporteurDetailTestCase(TestCase):
    def setUp(self):
        self.transporteur = factories.TransporteurFactory(siret=test.VALID_SIRET)
        self.detail_url = reverse('transporteurs_detail',
            kwargs={'transporteur_siret': test.VALID_SIRET})

    def test_get(self):
        response = self.client.get(self.detail_url)
        data = response.json()
        self.assertEqual(data['siret'], test.VALID_SIRET)
        self.assertEqual(data['raison_sociale'], self.transporteur.raison_sociale)
        self.assertEqual(data['completeness'], models.COMPLETENESS_PERCENT_MIN + 2 * models.EARNED_POINT_VALUE)
        self.assertEqual(data['working_area'], 'DEPARTEMENT')
        self.assertEqual(data['working_area_departements'], [35, 44])

    def test_get_empty_phone(self):
        self.transporteur.telephone = ''
        self.transporteur.save()
        response = self.client.get(self.detail_url)
        data = response.json()
        self.assertEqual(data['telephone'], '')

    def test_patch(self):
        NEW_PHONE = '+33240424546'
        NEW_EMAIL = 'foo@example.com'

        # Initial status
        self.assertNotEqual(self.transporteur.telephone, NEW_PHONE)
        self.assertNotEqual(self.transporteur.email, NEW_EMAIL)
        self.assertEqual(len(mail.outbox), 0)

        # Apply changes w/o working area
        with self.settings(MANAGERS=(("Foo", 'foo@example.com'))):
            response = self.client.patch(self.detail_url, json.dumps({
                'telephone': NEW_PHONE,
                'email': NEW_EMAIL,
            }), 'application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['telephone'], '02 40 42 45 46')
        self.assertEqual(data['email'], NEW_EMAIL)

        # Apply changes with working area
        with self.settings(MANAGERS=(("Foo", 'foo@example.com'))):
            response = self.client.patch(self.detail_url, json.dumps({
                'telephone': NEW_PHONE,
                'email': NEW_EMAIL,
                'working_area': models.WORKING_AREA_DEPARTEMENT,
                'working_area_departements': '23 45 ,,,67',
            }), 'application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Side effects
        self.assertEqual(data['telephone'], '02 40 42 45 46')
        self.assertEqual(data['email'], NEW_EMAIL)
        self.assertEqual(data['working_area'], models.WORKING_AREA_DEPARTEMENT)
        self.assertListEqual(data['working_area_departements'], [23, 45, 67])
        self.assertEqual(data['completeness'], 100)
        self.assertEqual(len(mail.outbox), 2)
        message = "[adock] Modification du transporteur %s" % self.transporteur.siret
        self.assertEqual(mail.outbox[0].subject, message)

    def test_invalid_patch_request(self):
        response = self.client.patch(self.detail_url, {'foo': 'foo'})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['message'], 'Seules les requêtes PATCH en JSON sont prises en charge.')

    def test_invalid_patch_payload(self):
        response = self.client.patch(self.detail_url, {'foo': 'foo'}, 'application/json')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['message'], 'Les données ne sont pas valides.')

    def test_invalid_phone(self):
        response = self.client.patch(self.detail_url, json.dumps({
            'telephone': '11223344556',
            'email': self.transporteur.email,
        }), 'application/json')
        self.assertEqual(response.status_code, 400)
        data = response.json()
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
