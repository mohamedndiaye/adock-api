from django.test import TestCase
from django.urls import reverse

from .. import factories as accounts_factories
from .. import jwt as accounts_jwt


class UserModelTestCase(TestCase):
    def test_custom_user_model(self):
        EMAIL = "foo@example.com"
        user = accounts_factories.UserFactory(email=EMAIL)
        self.assertEqual(user.email, EMAIL)
        self.assertEqual(user.get_username(), EMAIL)

    def test_jwt_payload_handler(self):
        """Should provide the JWT payload from a user instance"""
        user = accounts_factories.UserFactory()
        jwt_payload = accounts_jwt.jwt_payload_handler(user)
        self.assertEqual(jwt_payload["user_id"], user.pk)


class CreateUserTestCase(TestCase):
    def setUp(self):
        self.url = reverse("accounts_create")

    def test_success(self):
        response = self.client.post(
            self.url,
            {
                "email": "foo@example.com",
                "first_name": "Claude",
                "last_name": "Martin",
                "password": "secret1234",
            },
            content_type="application/json",
        )
        print(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"], "Compte utilisateur créé pour Claude Martin."
        )

    def test_failure(self):
        response = self.client.post(
            self.url,
            {"email": "bar.wrong", "first_name": "", "password": "short"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["email"], ["Saisissez une adresse email valable."])
        self.assertEqual(data["first_name"], ["Ce champ ne peut être vide."])
        self.assertEqual(data["last_name"], ["Ce champ est obligatoire."])
        self.assertEqual(
            data["password"],
            ["Assurez-vous que ce champ comporte au moins 8 caractères."],
        )
