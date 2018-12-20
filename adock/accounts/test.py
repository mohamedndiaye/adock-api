import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthTestCaseBase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User(email="courriel@fai.fr")
        self.user.set_password("password")
        self.user.save()

        url = reverse("accounts_log_in")
        data = {"email": self.user.email, "password": "password"}
        response = self.client.post(
            url, json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode("utf-8"))
        self.http_authorization = "Bearer " + content["token"]
