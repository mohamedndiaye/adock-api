from django.test import TestCase
from django.urls import reverse

from . import factories


class AccountsTestCase(TestCase):
    def test_csrf_token(self):
        url = reverse("accounts_get_csrf_token")
        response = self.client.get(url)
        data = response.json()
        self.assertIn("csrf_token", data)

    def test_custom_user_model(self):
        EMAIL = "foo@example.com"
        user = factories.UserFactory(email=EMAIL)
        self.assertEqual(user.email, EMAIL)
        self.assertEqual(user.get_username(), EMAIL)
