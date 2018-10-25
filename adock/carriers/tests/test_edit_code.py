# pylint: disable=W0201
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from . import test
from .. import factories


class CarrierEditCodeTestCase(test.CarrierTestCase):
    """
    An edit code (sent by mail) is required to be allowed to edit a locked carrier.
    """

    def setUp(self):
        self.carrier = factories.CarrierFactory(email_confirmed_at=timezone.now())

    def test_default_edit_code_expiration(self):
        self.assertTrue(self.carrier.is_locked())
        self.assertIsNone(self.carrier.edit_code)
        self.assertIsNone(self.carrier.edit_code_at)
        self.assertTrue(self.carrier.edit_code_has_expired())

    def test_valid_edit_code(self):
        self.carrier.set_edit_code()
        self.carrier.save()

        self.assertTrue(self.carrier.is_locked())
        self.assertFalse(self.carrier.edit_code_has_expired())

    def test_expired_edit_code(self):
        self.carrier.set_edit_code()
        self.carrier.edit_code_at -= settings.TRANSPORTEUR_EDIT_CODE_INTERVAL
        self.carrier.save()

        self.assertTrue(self.carrier.is_locked())
        self.assertTrue(self.carrier.edit_code_has_expired())

    def test_reset_edit_code(self):
        self.carrier.set_edit_code()
        self.assertIsNotNone(self.carrier.get_edit_code_timeout_at())
        self.carrier.reset_edit_code()
        self.assertIsNone(self.carrier.get_edit_code_timeout_at())

    def test_dont_send_edit_code(self):
        """Edit code shouldn't be sent to not confirmed address"""
        self.carrier.email_confirmed_at = None
        self.carrier.save()
        url = reverse(
            "carriers_envoyer_code", kwargs={"carrier_siret": self.carrier.siret}
        )
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(data["message"], "L'adresse électronique n'est pas confirmée.")

    def test_send_edit_code(self):
        url = reverse(
            "carriers_envoyer_code", kwargs={"carrier_siret": self.carrier.siret}
        )
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            data["message"], "Un code de modification a été envoyé par courriel."
        )
        self.assertEqual(data["email"], self.carrier.email)
        self.carrier.refresh_from_db()
        edit_code = self.carrier.edit_code
        self.assertEqual(len(str(edit_code)), 6)

        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            data["message"],
            "Le précédent code de modification envoyé est toujours valide.",
        )
        self.carrier.refresh_from_db()
        self.assertEqual(self.carrier.edit_code, edit_code)

    def test_patch_locked(self):
        self.detail_url = reverse(
            "carriers_detail", kwargs={"carrier_siret": self.carrier.siret}
        )

        self.carrier.set_edit_code()
        self.carrier.save()

        data = self.patch_carrier(
            {"telephone": "0102030405", "working_area_departements": "44"}, 400
        )
        self.assertEqual(
            data["edit_code"][0], "Le code de modification n'est pas valide."
        )

        self.patch_carrier(
            {
                "telephone": "0102030405",
                "working_area_departements": "44",
                "edit_code": self.carrier.edit_code,
            },
            200,
        )

    def test_patch_with_useless_edit_code(self):
        self.detail_url = reverse(
            "carriers_detail", kwargs={"carrier_siret": self.carrier.siret}
        )

        self.patch_carrier({"telephone": "0102030405", "edit_code": "666666"}, 400)

    def test_patch_email_reset_edit_code(self):
        self.carrier.email_confirmed_at = timezone.now()
        self.carrier.set_edit_code()
        self.carrier.save()

        self.detail_url = reverse(
            "carriers_detail", kwargs={"carrier_siret": self.carrier.siret}
        )
        self.patch_carrier(
            {
                "telephone": "0102030405",
                "email": "foo@example.com",
                "edit_code": self.carrier.edit_code,
            },
            200,
        )
        self.carrier.refresh_from_db()

        self.assertIsNone(self.carrier.email_confirmed_at)
        self.assertIsNone(self.carrier.edit_code)
        self.assertIsNone(self.carrier.edit_code_at)
        self.assertFalse(self.carrier.is_locked())
        self.assertTrue(self.carrier.edit_code_has_expired())
