import json

from django.test import TestCase
from django.urls import reverse

from adock.accounts import factories as accounts_factories


class AuthTestCase(TestCase):
    def setUp(self):
        self.user = accounts_factories.UserFactory(
            email="courriel@fai.fr", is_staff=True
        )
        self.user.set_password("password")
        self.user.save()

    def log_in(self, email=None, password=None):
        """Log in with email as username"""
        url = reverse("accounts_log_in")
        response = self.client.post(
            url,
            {
                "username": email if email is not None else self.user.username,
                "password": password if password is not None else "password",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return "Bearer " + response.json()["token"]
