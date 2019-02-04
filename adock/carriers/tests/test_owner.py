from django.test import TestCase

from adock.accounts import factories as accounts_factories

from .. import models
from .. import factories


class CarrierOnwerTestCase(TestCase):
    def test_model(self):
        carrier = factories.CarrierFactory()
        user = accounts_factories.UserFactory()
        self.assertFalse(carrier.has_owner())

        owner = carrier.add_owner(user)
        self.assertIsNotNone(owner.created_at)
        self.assertTrue(carrier.has_owner())

        # Didn't add twice
        owner = carrier.add_owner(user)
        self.assertEqual(models.CarrierUser.objects.count(), 1)

        self.assertEqual(user.carriers.first(), carrier)
