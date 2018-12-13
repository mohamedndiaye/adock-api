from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

class AuthTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User(email="courriel@fai.fr")
        self.user.set_password("password")
        self.user.save()

        url = reverse("accounts_log_in")
        data = {"username": self.user.email, "password": "password"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
