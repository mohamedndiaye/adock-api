from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .. import factories
from .. import tokens


class TransporteurDetailTestCase(TestCase):
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

    def test_send_edit_code(self):
        url = reverse('transporteurs_envoyer_code',
            kwargs={
                'transporteur_siret': self.transporteur.siret
            }
        )
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            data['message'],
            "Un code de modification vous a été envoyé par courriel."
        )
        self.transporteur.refresh_from_db()
        edit_code = self.transporteur.edit_code
        self.assertEqual(len(str(edit_code)), 6)

        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            data['message'],
            "Un code de modification a été déjà envoyé récemment."
        )
        self.transporteur.refresh_from_db()
        self.assertEqual(self.transporteur.edit_code, edit_code)

