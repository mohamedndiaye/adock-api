import requests_mock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from . import factories as accounts_factories
from . import jwt as accounts_jwt
from . import models as accounts_models
from . import views as accounts_views


class AccountsTestCase(TestCase):
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

    def test_france_connect_authorize(self):
        response = self.client.get(reverse("france_connect_authorize"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(settings.FRANCE_CONNECT_URLS["authorize"])
        )


class TestCreateOrUpdateUserTestCase(TestCase):
    def test_create_user(self):
        # Other not related user (no sub)
        accounts_factories.UserFactory(email="other@example.com")

        user_infos = {"email": "bar@example.com", "first_name": "Roger", "sub": "12345"}

        # The other_user has a different sub number so create a user
        user, created = accounts_views.create_or_update_user(user_infos)
        self.assertTrue(created)
        self.assertEqual(user.email, user_infos["email"])
        self.assertEqual(user.provider, accounts_models.PROVIDER_FRANCE_CONNECT)
        self.assertEqual(user.provider_data["sub"], user_infos["sub"])

    def test_update_user(self):
        accounts_factories.UserFactory(
            email="foo@example.com",
            provider=accounts_models.PROVIDER_FRANCE_CONNECT,
            provider_data={"sub": "12345"},
        )
        # Update an existing user
        user_infos = {"email": "bar@example.com", "first_name": "Roger", "sub": "12345"}
        user, created = accounts_views.create_or_update_user(user_infos)
        self.assertFalse(created)
        self.assertEqual(user.email, user_infos["email"])

    def test_creating_conflicting_user(self):
        accounts_factories.UserFactory(email="other@example.com")

        # Try to use an existing email
        user_infos = {
            "email": "other@example.com",
            "first_name": "Roger",
            "sub": "12345",
        }
        user, created = accounts_views.create_or_update_user(user_infos)
        self.assertIsNone(user)
        self.assertFalse(created)

    def test_updating_conflicting_user(self):
        accounts_factories.UserFactory(email="someone@example.com")
        accounts_factories.UserFactory(
            email="joe@example.com",
            provider=accounts_models.PROVIDER_FRANCE_CONNECT,
            provider_data={"sub": "12345"},
        )
        user_infos = {
            "email": "someone@example.com",
            "first_name": "Roger",
            "sub": "12345",
        }
        user, created = accounts_views.create_or_update_user(user_infos)
        self.assertFalse(created)
        # Unable to refresh_from_db with a error in current transaction
        # so the instance attributes are different in DB...
        self.assertEqual(user.email, user_infos["email"])


class FranceConnectCallbackTestCase(TestCase):
    def setUp(self):
        self.url = reverse("france_connect_callback")

    def test_unable_to_get_token(self):
        with requests_mock.mock() as m:
            m.post(settings.FRANCE_CONNECT_URLS["token"], status_code=404)
            response = self.client.get(self.url, {"code": "007"})
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(
            payload["message"], "Unable to get the token from France Connect."
        )

    def test_unable_to_get_user_infos(self):
        with requests_mock.mock() as m:
            m.post(
                settings.FRANCE_CONNECT_URLS["token"],
                status_code=200,
                json={"access_token": "123456789"},
            )
            m.get(settings.FRANCE_CONNECT_URLS["userinfo"], status_code=404)
            response = self.client.get(self.url, {"code": "007"})
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(
            payload["message"], "Unable to get the user infos from France Connect."
        )

    def test_create_user(self):
        with requests_mock.mock() as m:
            m.post(
                settings.FRANCE_CONNECT_URLS["token"],
                status_code=200,
                json={"access_token": "123456789"},
            )
            m.get(
                settings.FRANCE_CONNECT_URLS["userinfo"],
                status_code=200,
                json={
                    "email": "joe@example.com",
                    "sub": "1234",
                    "last_name": "MARTIN",
                    "birthdate": "1967-05-23",
                },
            )
            response = self.client.get(self.url, {"code": "007"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["message"], "OK")
