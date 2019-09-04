from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .. import models as accounts_models
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
        self.assertFalse(accounts_models.User.objects.exists())
        EMAIL = "foo@example.com"
        response = self.client.post(
            self.url,
            {
                "email": EMAIL,
                "first_name": "Claude",
                "last_name": "Martin",
                "password": "secret1234",
                "has_accepted_cgu": True,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"],
            (
                "Le compte utilisateur A Dock a été créé. "
                "Pour l'activer, cliquez sur le lien envoyé à votre adresse « %s »."
                % EMAIL
            ),
        )
        user = accounts_models.User.objects.get()
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            "[A Dock] Nouveau compte utilisateur %s" % user.email,
        )
        self.assertEqual(
            mail.outbox[1].subject,
            "[A Dock] Confirmation de votre adresse électronique",
        )

        self.assertEqual(user.email, EMAIL)
        self.assertEqual(user.has_accepted_cgu, True)

    def test_failure(self):
        response = self.client.post(
            self.url,
            {"email": "bar.wrong", "first_name": "", "password": "123456789"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertEqual(errors["email"], ["Saisissez une adresse email valable."])
        self.assertEqual(errors["first_name"], ["Ce champ ne peut être vide."])
        self.assertEqual(errors["last_name"], ["Ce champ est obligatoire."])
        self.assertEqual(
            errors["has_accepted_cgu"],
            [
                "Vous devez accepter les Conditions Générales d'Utilisation pour utiliser le service."
            ],
        )
        self.assertEqual(
            errors["password"],
            [
                "Ce mot de passe est trop courant.",
                "Ce mot de passe est entièrement numérique.",
            ],
        )


class ActivateUserTestCase(TestCase):
    def setUp(self):
        self.user = accounts_factories.UserFactory(is_active=False)

    def test_no_user(self):
        url = reverse(
            "accounts_activate",
            kwargs={"user_id": self.user.pk + 1, "user_token": "foo"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "L'utilisateur n'existe pas.")

    def test_already_active(self):
        self.user.is_active = True
        self.user.save()
        url = reverse(
            "accounts_activate", kwargs={"user_id": self.user.pk, "user_token": "foo"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"], "Le compte utilisateur est déjà actif."
        )

    def test_invalid_token(self):
        url = reverse(
            "accounts_activate", kwargs={"user_id": self.user.pk, "user_token": "foo"}
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
                "user_token": accounts_tokens.account_token_generator.make_token(
                    self.user
                ),
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"],
            "%s %s, votre compte utilisateur A Dock est à présent actif !"
            % (self.user.first_name, self.user.last_name),
        )


class RecoverPasswordTestCase(TestCase):
    def setUp(self):
        self.url = reverse("accounts_recover_password")

    def test_no_email(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)

    def test_not_active_user(self):
        user = accounts_factories.UserFactory(is_active=False)
        response = self.client.post(
            self.url, {"email": user.email}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_wrong_provider(self):
        user = accounts_factories.UserFactory(
            is_active=True, provider=accounts_models.PROVIDER_FRANCE_CONNECT
        )
        response = self.client.post(
            self.url, {"email": user.email}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"], "L'adresse électronique est introuvable."
        )
