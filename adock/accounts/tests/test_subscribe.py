from django.test import TestCase
from django.urls import reverse

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
