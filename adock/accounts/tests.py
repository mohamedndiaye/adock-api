from django.test import TestCase
from django.urls import reverse


class AccountsTestCase(TestCase):
    def test_csrf(self):
        url = reverse("accounts_get_csrf")
        response = self.client.get(url)
        data = response.json()
        self.assertIn("token", data)
