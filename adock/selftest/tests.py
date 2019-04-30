from django.urls import reverse

from adock.accounts.test import AuthTestCase
from adock.accounts import factories as accounts_factories


class SelftestTestCase(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("selftest")

    def test_no_logged(self):
        response = self.client.get(self.url, content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_staff_only(self):
        user = accounts_factories.UserFactory(
            email="courriel@example.com", is_staff=False
        )
        user.set_password("password")
        user.save()

        http_authorization = self.log_in(user.email, "password")
        response = self.client.get(
            self.url,
            content_type="application/json",
            HTTP_AUTHORIZATION=http_authorization,
        )
        self.assertEqual(response.status_code, 403)

    def test_selftest(self):
        http_authorization = self.log_in()
        url = reverse("selftest")
        response = self.client.get(
            url, content_type="application/json", HTTP_AUTHORIZATION=http_authorization
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("actions", response.json())
