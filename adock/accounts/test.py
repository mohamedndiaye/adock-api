from django.contrib.auth import models as auth_models
from django.test import TestCase
from django.urls import reverse


class AuthTestCase(TestCase):
    def setUp(self):
        self.user = auth_models.User(username="username")
        self.user.set_password("password")
        self.user.save()

        url = reverse("accounts_log_in")
        data = {"username": "username", "password": "password"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
