from django.test import TestCase
from django.urls import reverse

from .. import factories as accounts_factories
from .. import jwt as accounts_jwt
from .. import tokens as accounts_tokens


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

    def test_create(self):
        EMAIL = "foo@example.com"
        response = self.client.post(
            self.url,
            {
                "email": EMAIL,
                "first_name": "Claude",
                "last_name": "Martin",
                "password": "secret1234",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"], "Un email vous a été envoyé à « %s »." % EMAIL
        )

    def test_failure(self):
        response = self.client.post(
            self.url,
            {"email": "bar.wrong", "first_name": "", "password": "short"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertEqual(errors["email"], ["Saisissez une adresse email valable."])
        self.assertEqual(errors["first_name"], ["Ce champ ne peut être vide."])
        self.assertEqual(errors["last_name"], ["Ce champ est obligatoire."])
        self.assertEqual(
            errors["password"],
            ["Assurez-vous que ce champ comporte au moins 8 caractères."],
        )


class ActivateUserTestCase(TestCase):
    def setUp(self):
        self.user = accounts_factories.UserFactory(is_active=False)

    def test_no_user(self):
        url = reverse(
            "accounts_activate", kwargs={"user_id": self.user.pk + 1, "token": "foo"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "L'utilisateur n'existe pas.")

    def test_already_active(self):
        self.user.is_active = True
        self.user.save()
        url = reverse(
            "accounts_activate", kwargs={"user_id": self.user.pk, "token": "foo"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"], "Le compte utilisateur est déjà actif."
        )

    def test_invalid_token(self):
        url = reverse(
            "accounts_activate", kwargs={"user_id": self.user.pk, "token": "foo"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"], "Le jeton d'activation n'est pas valide."
        )

    def test_activate(self):
        url = reverse(
            "accounts_activate",
            kwargs={
                "user_id": self.user.pk,
                "token": accounts_tokens.account_activation_token.make_token(self.user),
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"], "Le compte utilisateur est activé."
        )
