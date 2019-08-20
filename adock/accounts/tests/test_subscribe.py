import re

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from adock.accounts import models as accounts_models
from adock.carriers import models as carriers_models
from adock.carriers import factories as carriers_factories


class SubscribeWorkflowTestCase(TestCase):
    def setUp(self):
        self.carrier = carriers_factories.CarrierFactory(
            enseigne="MA PETITE ENTREPRISE", with_editable=True
        )

    def test_workflow(self):
        # 1 - select a carrier
        search_url = reverse("carriers_search")
        response = self.client.get(search_url, {"q": "Petite"})
        self.assertEqual(response.status_code, 200)
        carrier_data = response.json()["carriers"][0]
        self.assertEqual(carrier_data["enseigne"], self.carrier.enseigne)

        # 2 - create an account
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
                "send_activation_link": False,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            data["message"], "Le compte utilisateur « %s » a été créé." % EMAIL
        )

        user = accounts_models.User.objects.get()
        self.assertEqual(user.email, EMAIL)
        self.assertFalse(user.is_active)

        # Mail sent to managers
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "[A Dock] Nouveau compte utilisateur %s" % user.email,
        )

        mail.outbox = []

        # 3 - edit the carrier (same email address as user)
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
            "[A Dock] Notification de modification de votre fiche transporteur",
        )
        # ii
        self.assertEqual(
            mail.outbox[1].subject,
            "[A Dock] En attente de confirmation de votre compte et vos modifications",
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
            "[A Dock] Modification du transporteur %s" % self.carrier.siret,
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
        self.assertEqual(data["message"], "Le compte utilisateur est activé.")

        user.refresh_from_db()
        self.assertTrue(user.is_active)

        self.carrier.refresh_from_db()
        self.assertEqual(self.carrier.editable, carrier_editable)
