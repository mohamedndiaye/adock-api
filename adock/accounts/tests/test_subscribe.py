import re

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from adock.accounts import models as accounts_models
from adock.accounts import test as accounts_test
from adock.carriers import factories as carriers_factories
from adock.carriers import models as carriers_models
from adock.carriers.tests import test as carriers_test


class CreateAccountSubscribeWorkflowTestCase(TestCase):
    def setUp(self):
        self.carrier = carriers_factories.CarrierFactory(
            enseigne="MA PETITE ENTREPRISE", with_editable=True
        )

    def test_workflow(self):
        # Step 1 - select a carrier
        search_url = reverse("carriers_search")
        response = self.client.get(search_url, {"q": "Petite"})
        self.assertEqual(response.status_code, 200)
        carrier_data = response.json()["carriers"][0]
        self.assertEqual(carrier_data["enseigne"], self.carrier.enseigne)

        # Step 2 - create an account
        create_account_url = reverse("accounts_create")
        EMAIL = "foo@example.com"
        response = self.client.post(
            create_account_url,
            {
                "email": EMAIL,
                "first_name": "Jean-Yves",
                "last_name": "Ménard",
                "password": "secret1234",
                "has_accepted_cgu": True,
                # No confirmation mail
                "send_activation_link": False,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Le compte utilisateur A Dock a été créé.")

        user = accounts_models.User.objects.get()
        self.assertEqual(user.email, EMAIL)
        self.assertFalse(user.is_active)

        # Mail sent to managers
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "[A Dock] log - Nouveau compte utilisateur %s" % user.email,
        )

        mail.outbox = []

        # Step 3 - edit the carrier (same email address as user)
        carrier_url = reverse(
            "carriers_detail", kwargs={"carrier_siret": self.carrier.siret}
        )
        response = self.client.post(
            carrier_url,
            {"email": EMAIL, "telephone": "+33240424546", "created_by_email": EMAIL},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["confirmation_sent_to"], EMAIL)
        self.assertIsNone(data["account_confirmation_sent_to"])
        carrier_editable = carriers_models.CarrierEditable.objects.get(email=EMAIL)
        self.assertEqual(carrier_editable.created_by.email, EMAIL)

        # Mails:
        # i - old address
        # ii - one for user and changes to new user
        # iii - changes to managers
        self.assertEqual(len(mail.outbox), 3)

        # i - old
        self.assertEqual(
            mail.outbox[0].subject,
            "[A Dock] Notification de modification de votre fiche entreprise",
        )
        # ii
        self.assertEqual(
            mail.outbox[1].subject,
            "[A Dock] Activez votre compte utilisateur et confirmez votre fiche entreprise",
        )

        # Search UI URL
        ui_confirm_url_search = re.search(
            r"%sutilisateur/(?P<user_id>\d+)/activer/(?P<user_token>.+)/transporteur/changement/(?P<carrier_editable_id>\d+)/confirmer/(?P<carrier_editable_token>.+)/"
            % settings.HTTP_CLIENT_URL,
            mail.outbox[1].body,
        )
        self.assertIsNotNone(ui_confirm_url_search)

        results = ui_confirm_url_search.groupdict()
        self.assertEqual(user.pk, int(results["user_id"]))
        self.assertEqual(carrier_editable.pk, int(results["carrier_editable_id"]))

        # iii
        self.assertEqual(
            mail.outbox[2].subject,
            "[A Dock] log - Modification du transporteur %s" % self.carrier.siret,
        )

        # Resolve server URL
        confirm_url = reverse(
            "accounts_activate_with_carrier_editable",
            kwargs={
                "user_id": results["user_id"],
                "user_token": results["user_token"],
                "carrier_editable_id": results["carrier_editable_id"],
                "carrier_editable_token": results["carrier_editable_token"],
            },
        )
        response = self.client.get(confirm_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            data["message"],
            (
                "Jean-Yves Ménard, votre compte utilisateur A Dock est à présent actif ! "
                "Les changements de la fiche entreprise ont été appliqué avec succès."
            ).format(email=EMAIL),
        )

        user.refresh_from_db()
        self.assertTrue(user.is_active)

        self.carrier.refresh_from_db()
        self.assertEqual(self.carrier.editable, carrier_editable)


class LoggedSubscribeWorkflowTestCase(
    accounts_test.AuthTestCase, carriers_test.CarrierTestCaseMixin
):
    def setUp(self):
        super().setUp()
        self.carrier = carriers_factories.CarrierFactory(
            enseigne="MA PETITE ENTREPRISE", with_editable=True
        )
        self.http_authorization = self.log_in()
        self.carrier_detail_url = reverse(
            "carriers_detail", kwargs={"carrier_siret": self.carrier.siret}
        )

    def test_workflow(self):
        # Step 1 is identical to previous test
        # Step 2 - Logged in with FC account
        # step 3 - edit the carrier
        data = self.post_carrier_logged(
            {
                "email": "carrier@example.com",
                "telephone": "+33240424546",
                # User is logged so the field will be ignored
                "created_by_email": "user@example.com",
            },
            200,
        )
        self.assertEqual(data["confirmation_sent_to"], "carrier@example.com")
        self.assertIsNone(data["account_confirmation_sent_to"])

        # Mails
        # i - old address
        # ii - one for changes to carrier
        # ii -  changes to managers
        self.assertEqual(len(mail.outbox), 3)

        # i - old
        self.assertEqual(
            mail.outbox[0].subject,
            "[A Dock] Notification de modification de votre fiche entreprise",
        )
        # ii
        self.assertEqual(
            mail.outbox[1].subject,
            "[A Dock] Confirmez la mise à jour de votre fiche entreprise",
        )
        # iii
        self.assertEqual(
            mail.outbox[2].subject,
            "[A Dock] log - Modification du transporteur %s" % self.carrier.siret,
        )
