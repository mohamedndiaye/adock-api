from django.test import TestCase

from . import factories as accounts_factories
from . import jwt as accounts_jwt


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
