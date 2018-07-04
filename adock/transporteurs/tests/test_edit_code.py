from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .. import factories
from . import test


class TransporteurEditCodeTestCase(test.TransporteurTestCase):
    """
    An edit code (sent by mail) is required to be allowed to edit a locked transporteur.
    """
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            data['message'],
            "Un code de modification a été déjà envoyé récemment."
        )
        self.transporteur.refresh_from_db()
        self.assertEqual(self.transporteur.edit_code, edit_code)

    def test_patch_locked(self):
        self.detail_url = reverse(
            'transporteurs_detail',
            kwargs={'transporteur_siret': self.transporteur.siret}
        )

        self.transporteur.set_edit_code()
        self.transporteur.save()

        data = self.patch_transporteur(
            {
                'telephone': '0102030405',
                'working_area_departements': '44',
            },
            400
        )
        self.assertEqual(
            data['edit_code'][0],
            "Le code de modification n'est pas valide."
        )

        self.patch_transporteur(
            {
                'telephone': '0102030405',
                'working_area_departements': '44',
                'edit_code': self.transporteur.edit_code
            },
            200
        )

    def test_patch_with_useless_edit_code(self):
        self.detail_url = reverse(
            'transporteurs_detail',
            kwargs={'transporteur_siret': self.transporteur.siret}
        )

        self.patch_transporteur(
            {
                'telephone': '0102030405',
                'edit_code': '666666',
            },
            400
        )
