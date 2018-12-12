from django.test import TestCase
from django.urls import reverse


class AccountsTestCase(TestCase):
    def test_csrf_token(self):
        url = reverse("accounts_get_csrf_token")
        response = self.client.get(url)
        data = response.json()
        self.assertIn("csrf_token", data)
