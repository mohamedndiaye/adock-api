import requests_mock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from jwt_auth import views as jwt_auth_views

from .. import factories as accounts_factories
from .. import models as accounts_models
from .. import views as accounts_views


class FranceConnectCreateOrUpdateUserTestCase(TestCase):
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
            username="12345",
            email="foo@example.com",
            provider=accounts_models.PROVIDER_FRANCE_CONNECT,
            provider_data={"sub": "12345"},
        )
        # Update an existing user
        user_infos = {"sub": "12345", "email": "bar@example.com", "first_name": "Roger"}
        user, created = accounts_views.create_or_update_user(user_infos)
        self.assertFalse(created)
        self.assertEqual(user.email, user_infos["email"])

    def test_create_with_used_email(self):
        """Try to use an existing email with a different username"""
        accounts_factories.UserFactory(email="other@example.com")
        user_infos = {
            "email": "other@example.com",
            "first_name": "Roger",
            "sub": "12345",
        }
        user, created = accounts_views.create_or_update_user(user_infos)
        self.assertTrue(created)
        self.assertEqual(user.email, user_infos["email"])

    def test_updating_conflicting_user(self):
        accounts_factories.UserFactory(email="someone@example.com")
        accounts_factories.UserFactory(
            username="12345",
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


class FranceConnectLoginTestCase(TestCase):
    def setUp(self):
        self.authorize_url = reverse("france_connect_authorize")
        self.callback_url = reverse("france_connect_callback")

    def get_state_from_response(self, response):
        # Extact query params
        query_strings = dict(
            [
                query_string.split("=")
                for query_string in response.url.split("?")[1].split("&")
            ]
        )
        return query_strings["state"]

    def test_authorize(self):
        response = self.client.get(self.authorize_url, {"nonce": "fakednonce"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(settings.FRANCE_CONNECT_URLS["authorize"])
        )
        self.assertIn("state=", response.url)
        self.assertIn("scope=", response.url)

    def test_no_code(self):
        response = self.client.get(self.callback_url)
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(
            payload["message"], "La requête ne contient pas le paramètre « code »."
        )

    def test_no_state(self):
        response = self.client.get(self.callback_url, {"code": "fake"})
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["message"], "Le paramètre « state » n'est pas valide.")

    def test_invalid_state(self):
        response = self.client.get(
            self.callback_url, {"code": "fake", "state": "doesnotexist"}
        )
        self.assertEqual(response.status_code, 400)

    def test_unable_to_get_token(self):
        response = self.client.get(self.authorize_url, {"nonce": "fake"})
        state = self.get_state_from_response(response)
        with requests_mock.mock() as m:
            m.post(settings.FRANCE_CONNECT_URLS["token"], status_code=404)
            response = self.client.get(
                self.callback_url, {"code": "007", "state": state}
            )
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(
            payload["message"], "Impossible d'obtenir le jeton de FranceConnect."
        )

    def test_unable_to_get_user_infos(self):
        response = self.client.get(self.authorize_url, {"nonce": "fake"})
        state = self.get_state_from_response(response)
        with requests_mock.mock() as m:
            m.post(
                settings.FRANCE_CONNECT_URLS["token"],
                status_code=200,
                json={"access_token": "123456789"},
            )
            m.get(settings.FRANCE_CONNECT_URLS["userinfo"], status_code=404)
            response = self.client.get(
                self.callback_url, {"code": "007", "state": state}
            )
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(
            payload["message"],
            "Impossible d'obtenir les informations utilisateur de FranceConnect.",
        )

    def test_create_user(self):
        # Create a state in DB and return it
        response = self.client.get(self.authorize_url, {"nonce": "fake"})
        state = self.get_state_from_response(response)
        with requests_mock.mock() as m:
            m.post(
                settings.FRANCE_CONNECT_URLS["token"],
                status_code=200,
                json={
                    "access_token": "123456789",
                    "token_type": "Bearer",
                    "expires_in": 60,
                    "id_token": "VeryLongToken",
                },
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
            response = self.client.get(
                self.callback_url, {"code": "007", "state": state}
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["token_type"], "Bearer")
        self.assertIn("token", payload)
        self.assertIn("expires_in", payload)
        self.assertIn("id_token", payload)


class FranceConnectLogoutTestCase(TestCase):
    def setUp(self):
        self.user = accounts_factories.UserFactory()
        self.url = reverse("france_connect_logout")

    def test_no_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"], "L'utilisateur n'est pas authentifié."
        )

    def test_not_id_token(self):
        token = jwt_auth_views.jwt_encode_token(self.user)
        response = self.client.get(
            self.url, **{"HTTP_AUTHORIZATION": "Bearer %s" % token}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "L'utilisateur est déconnecté.")

    def test_logout_error(self):
        token = jwt_auth_views.jwt_encode_token(self.user)
        id_token = "54321"
        with requests_mock.mock() as m:
            m.get(
                settings.FRANCE_CONNECT_URLS["logout"] + "?" + id_token, status_code=400
            )
            response = self.client.get(
                self.url,
                {"id_token": id_token},
                **{"HTTP_AUTHORIZATION": "Bearer %s" % token}
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"],
            "Impossible de déconnecter l'utilisateur de FranceConnect.",
        )

    def test_logout_success(self):
        token = jwt_auth_views.jwt_encode_token(self.user)
        id_token = "54321"
        with requests_mock.mock() as m:
            m.get(
                settings.FRANCE_CONNECT_URLS["logout"] + "?" + id_token, status_code=200
            )
            response = self.client.get(
                self.url,
                {"id_token": id_token},
                **{"HTTP_AUTHORIZATION": "Bearer %s" % token}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "L'utilisateur est déconnecté.")
