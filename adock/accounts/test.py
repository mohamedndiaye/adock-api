import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from adock.accounts import factories as accounts_factories


class AuthTestCaseBase(TestCase):
    def setUp(self):
        self.user = accounts_factories.UserFactory(
            email="courriel@fai.fr", is_staff=True
        )
        self.user.set_password("password")
        self.user.save()

    def log_in(self, email=None, password=None):
        """Log in with email as username"""
        url = reverse("accounts_log_in")
        data = {
            "username": email if email is not None else self.user.username,
            "password": password if password is not None else "password",
        }
        response = self.client.post(
            url, json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode("utf-8"))
        return "Bearer " + content["token"]
