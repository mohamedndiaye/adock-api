from django.utils import timezone
from django.urls import reverse

from .. import factories
from .. import tokens
from . import test


class TransporteurEmailConfirmationTestCase(test.TransporteurTestCase):
    def setUp(self):
        self.transporteur = factories.TransporteurFactory()

    def test_idempotent_token(self):
        token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.assertIsNotNone(token)
        self.assertNotEqual(token, '')
        same_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.assertEqual(token, same_token)

    def test_changed_siret_token(self):
        old_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.transporteur.siret = str(int(self.transporteur.siret) + 1)[:15]
        new_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.assertNotEqual(old_token, new_token)

    def test_changed_email_token(self):
        old_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.transporteur.email = 'foo@example.com'
        new_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.assertNotEqual(old_token, new_token)

    def test_already_confirmed_email_token(self):
        old_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.transporteur.email_confirmed_at = timezone.now()
        new_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.assertNotEqual(old_token, new_token)

    def test_confirm_token(self):
        self.assertFalse(self.transporteur.is_locked())
        token = tokens.email_confirmation_token.make_token(self.transporteur)
        url = reverse(
            'transporteurs_confirmer_adresse',
            kwargs={
                'transporteur_siret': self.transporteur.siret,
                'token': token
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            data['message'],
            "L'adresse électronique est confirmée."
        )
        self.transporteur.refresh_from_db()
        self.assertTrue(self.transporteur.is_locked())

    def test_altered_token(self):
        token = tokens.email_confirmation_token.make_token(self.transporteur)
        url = reverse(
            'transporteurs_confirmer_adresse',
            kwargs={
                'transporteur_siret': self.transporteur.siret,
                'token': token + 'z'
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_changed_email(self):
        self.transporteur.email_confirmed_at = timezone.now()
        self.assertTrue(self.transporteur.is_locked())
        self.detail_url = reverse(
            'transporteurs_detail',
            kwargs={'transporteur_siret': self.transporteur.siret}
        )
        transporteur = self.patch_transporteur(
            {
                'telephone': '0102030405',
                'email': 'bar@example.com',
            },
            200
        )
        self.assertFalse(transporteur['is_locked'])
        self.transporteur.refresh_from_db()
        self.assertFalse(self.transporteur.is_locked())
        self.assertIsNone(self.transporteur.email_confirmed_at)
