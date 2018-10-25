from django.core import mail
from django.urls import reverse

from . import test
from .. import factories, tokens


class CarrierEmailConfirmationTestCase(test.CarrierTestCase):
    def setUp(self):
        self.carrier = factories.CarrierFactory()
        self.detail_url = reverse(
            "carriers_detail", kwargs={"carrier_siret": self.carrier.siret}
        )

    def test_idempotent_token(self):
        token = tokens.email_confirmation_token.make_token(self.carrier)
        self.assertIsNotNone(token)
        self.assertNotEqual(token, "")
        same_token = tokens.email_confirmation_token.make_token(self.carrier)
        self.assertEqual(token, same_token)

    def test_changed_siret_token(self):
        old_token = tokens.email_confirmation_token.make_token(self.carrier)
        self.carrier.siret = str(int(self.carrier.siret) + 1)[:15]
        new_token = tokens.email_confirmation_token.make_token(self.carrier)
        self.assertNotEqual(old_token, new_token)

    def test_changed_email_token(self):
        old_token = tokens.email_confirmation_token.make_token(self.carrier)
        self.carrier.email = "foo@example.com"
        new_token = tokens.email_confirmation_token.make_token(self.carrier)
        self.assertNotEqual(old_token, new_token)

    def test_already_confirmed_email_token(self):
        old_token = tokens.email_confirmation_token.make_token(self.carrier)
        self.carrier.lock()
        new_token = tokens.email_confirmation_token.make_token(self.carrier)
        self.assertNotEqual(old_token, new_token)

    def test_confirm_token(self):
        self.assertFalse(self.carrier.is_locked())
        token = tokens.email_confirmation_token.make_token(self.carrier)
        url = reverse(
            "carriers_confirm_email",
            kwargs={"carrier_siret": self.carrier.siret, "token": token},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "L'adresse électronique est confirmée.")
        self.carrier.refresh_from_db()
        self.assertTrue(self.carrier.is_locked())

        self.assertEqual(len(mail.outbox), 1)
        subject = "[adock] Verrouillage du transporteur %s" % self.carrier.siret
        self.assertEqual(mail.outbox[0].subject, subject)

    def test_altered_token(self):
        token = tokens.email_confirmation_token.make_token(self.carrier)
        url = reverse(
            "carriers_confirm_email",
            kwargs={"carrier_siret": self.carrier.siret, "token": token + "z"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_validated_carrier_wo_mail(self):
        self.assertIsNone(self.carrier.validated_at)
        self.carrier.email = ""
        self.carrier.save()

        self.patch_carrier({"telephone": "0102030405"}, 200)
        self.assertEqual(len(mail.outbox), 1)
        message = "[adock] Modification du transporteur %s" % self.carrier.siret
        self.assertEqual(mail.outbox[0].subject, message)
        self.carrier.refresh_from_db()
        self.assertIsNotNone(self.carrier.validated_at)

    def test_validated_carrier_with_mail(self):
        self.assertIsNone(self.carrier.validated_at)
        self.assertGreaterEqual(len(self.carrier.email), 1)

        self.patch_carrier({"telephone": "0102030405"}, 200)
        self.assertEqual(len(mail.outbox), 2)
        message = "[adock] Modification du transporteur %s" % self.carrier.siret
        self.assertEqual(mail.outbox[0].subject, message)
        self.assertEqual(
            mail.outbox[1].subject,
            "A Dock - Confirmation de votre adresse électronique",
        )
        self.carrier.refresh_from_db()
        self.assertIsNotNone(self.carrier.validated_at)

    def test_changed_email(self):
        self.carrier.lock()
        self.carrier.save()
        self.assertTrue(self.carrier.is_locked())

        self.detail_url = reverse(
            "carriers_detail", kwargs={"carrier_siret": self.carrier.siret}
        )
        # Unable to change it w/o edit code
        data = self.patch_carrier(
            {"telephone": "0102030405", "email": "bar@example.com"}, 400
        )

        self.carrier.set_edit_code()
        self.carrier.save()
        # Invalidate previous lock by changing email
        data = self.patch_carrier(
            {
                "telephone": "0102030405",
                "email": "bar@example.com",
                "edit_code": self.carrier.edit_code,
            },
            200,
        )
        self.assertFalse(data["carrier"]["is_locked"])
        self.carrier.refresh_from_db()
        self.assertFalse(self.carrier.is_locked())
        self.assertIsNone(self.carrier.email_confirmed_at)
