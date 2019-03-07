import json

from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from adock.accounts.test import AuthTestCaseBase
from adock.carriers import factories as carriers_factories


class ProfileTestCase(AuthTestCaseBase):
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
        self.user.refresh_from_db()
        self.assertEqual(
            json.dumps(self.user.last_login, cls=DjangoJSONEncoder).strip('"'),
            data["user"]["last_login"],
        )
        self.assertEqual(self.user.provider, data["user"]["provider"])
        self.assertEqual(carrier.siret, data["user"]["carriers"][0]["siret"])
