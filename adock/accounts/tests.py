from django.test import TestCase
from django.urls import reverse

from . import factories


class AccountsTestCase(TestCase):
    def test_custom_user_model(self):
        EMAIL = "foo@example.com"
        user = factories.UserFactory(email=EMAIL)
        self.assertEqual(user.email, EMAIL)
        self.assertEqual(user.get_username(), EMAIL)
