from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .. import factories
from .. import tokens


class TransporteurEmailConfirmationTestCase(TestCase):
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


class TransporteurEditCodeTestCase(TestCase):
    def setUp(self):
        self.transporteur = factories.TransporteurFactory(
            email_confirmed_at=timezone.now()
        )

    def test_default_edit_code_expiration(self):
        self.assertTrue(self.transporteur.is_locked())
        self.assertIsNone(self.transporteur.edit_code)
        self.assertIsNone(self.transporteur.edit_code_at)
        self.assertTrue(self.transporteur.edit_code_has_expired())

    def test_valid_edit_code(self):
        self.transporteur.set_edit_code()
        self.transporteur.save()

        self.assertTrue(self.transporteur.is_locked())
        self.assertFalse(self.transporteur.edit_code_has_expired())

    def test_expired_edit_code(self):
        self.transporteur.set_edit_code()
        self.transporteur.edit_code_at -= settings.TRANSPORTEUR_EDIT_CODE_INTERVAL
        self.transporteur.save()

        self.assertTrue(self.transporteur.is_locked())
        self.assertTrue(self.transporteur.edit_code_has_expired())

    def test_dont_send_edit_code(self):
        """Edit code shouldn't be sent to not confirmed address"""
        self.transporteur.email_confirmed_at = None
        self.transporteur.save()
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
            "La fiche est en libre accès."
        )

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

