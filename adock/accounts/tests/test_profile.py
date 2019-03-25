import json

from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from adock.accounts.test import AuthTestCase
from adock.carriers import factories as carriers_factories


class ProfileTestCase(AuthTestCase):
    def setUp(self):
        self.url = reverse("accounts_profile")
        super().setUp()

    def test_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_profile(self):
        carrier = carriers_factories.CarrierFactory(
            with_editable={"created_by": self.user}
        )
        http_authorization = self.log_in()
        response = self.client.get(self.url, HTTP_AUTHORIZATION=http_authorization)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # For last log in
        self.user.refresh_from_db()
        self.assertEqual(
            json.dumps(self.user.last_login, cls=DjangoJSONEncoder).strip('"'),
            data["user"]["last_login"],
        )
        self.assertEqual(self.user.provider, data["user"]["provider"])
        self.assertTrue(data["user"]["has_accepted_cgu"])
        self.assertTrue(data["user"]["is_staff"])
        self.assertNotIn("carriers", data["user"])

        url_extended = reverse("accounts_profile_extended")
        response = self.client.get(url_extended, HTTP_AUTHORIZATION=http_authorization)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(carrier.siret, data["user"]["carriers"][0]["siret"])

    def test_patch_profile(self):
        self.user.has_accepted_cgu = False
        self.user.save()

        http_authorization = self.log_in()

        # Accept CGU
        response = self.client.patch(
            self.url,
            {"has_accepted_cgu": True},
            content_type="application/json",
            HTTP_AUTHORIZATION=http_authorization,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["user"]["has_accepted_cgu"])

        # Try to revoke CGU
        response = self.client.patch(
            self.url,
            {"has_accepted_cgu": False},
            content_type="application/json",
            HTTP_AUTHORIZATION=http_authorization,
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("has_accepted_cgu", data["errors"])
