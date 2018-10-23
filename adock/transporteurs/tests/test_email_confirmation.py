from django.core import mail
from django.urls import reverse

from . import test
from .. import factories, tokens


class TransporteurEmailConfirmationTestCase(test.TransporteurTestCase):
    def setUp(self):
        self.transporteur = factories.TransporteurFactory()
        self.detail_url = reverse(
            "transporteurs_detail",
            kwargs={"transporteur_siret": self.transporteur.siret},
        )

    def test_idempotent_token(self):
        token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.assertIsNotNone(token)
        self.assertNotEqual(token, "")
        same_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.assertEqual(token, same_token)

    def test_changed_siret_token(self):
        old_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.transporteur.siret = str(int(self.transporteur.siret) + 1)[:15]
        new_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.assertNotEqual(old_token, new_token)

    def test_changed_email_token(self):
        old_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.transporteur.email = "foo@example.com"
        new_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.assertNotEqual(old_token, new_token)

    def test_already_confirmed_email_token(self):
        old_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.transporteur.lock()
        new_token = tokens.email_confirmation_token.make_token(self.transporteur)
        self.assertNotEqual(old_token, new_token)

    def test_confirm_token(self):
        self.assertFalse(self.transporteur.is_locked())
        token = tokens.email_confirmation_token.make_token(self.transporteur)
        url = reverse(
            "transporteurs_confirmer_adresse",
            kwargs={"transporteur_siret": self.transporteur.siret, "token": token},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "L'adresse électronique est confirmée.")
        self.transporteur.refresh_from_db()
        self.assertTrue(self.transporteur.is_locked())

        self.assertEqual(len(mail.outbox), 1)
        subject = "[adock] Verrouillage du transporteur %s" % self.transporteur.siret
        self.assertEqual(mail.outbox[0].subject, subject)

    def test_altered_token(self):
        token = tokens.email_confirmation_token.make_token(self.transporteur)
        url = reverse(
            "transporteurs_confirmer_adresse",
            kwargs={
                "transporteur_siret": self.transporteur.siret,
                "token": token + "z",
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_validated_transporteur_wo_mail(self):
        self.assertIsNone(self.transporteur.validated_at)
        self.transporteur.email = ""
        self.transporteur.save()

        self.patch_transporteur({"telephone": "0102030405"}, 200)
        self.assertEqual(len(mail.outbox), 1)
        message = "[adock] Modification du transporteur %s" % self.transporteur.siret
        self.assertEqual(mail.outbox[0].subject, message)
        self.transporteur.refresh_from_db()
        self.assertIsNotNone(self.transporteur.validated_at)

    def test_validated_transporteur_with_mail(self):
        self.assertIsNone(self.transporteur.validated_at)
        self.assertGreaterEqual(len(self.transporteur.email), 1)

        self.patch_transporteur({"telephone": "0102030405"}, 200)
        self.assertEqual(len(mail.outbox), 2)
        message = "[adock] Modification du transporteur %s" % self.transporteur.siret
        self.assertEqual(mail.outbox[0].subject, message)
        self.assertEqual(
            mail.outbox[1].subject,
            "A Dock - Confirmation de votre adresse électronique",
        )
        self.transporteur.refresh_from_db()
        self.assertIsNotNone(self.transporteur.validated_at)

    def test_changed_email(self):
        self.transporteur.lock()
        self.transporteur.save()
        self.assertTrue(self.transporteur.is_locked())

        self.detail_url = reverse(
            "transporteurs_detail",
            kwargs={"transporteur_siret": self.transporteur.siret},
        )
        # Unable to change it w/o edit code
        data = self.patch_transporteur(
            {"telephone": "0102030405", "email": "bar@example.com"}, 400
        )

        self.transporteur.set_edit_code()
        self.transporteur.save()
        # Invalidate previous lock by changing email
        data = self.patch_transporteur(
            {
                "telephone": "0102030405",
                "email": "bar@example.com",
                "edit_code": self.transporteur.edit_code,
            },
            200,
        )
        self.assertFalse(data["transporteur"]["is_locked"])
        self.transporteur.refresh_from_db()
        self.assertFalse(self.transporteur.is_locked())
        self.assertIsNone(self.transporteur.email_confirmed_at)
