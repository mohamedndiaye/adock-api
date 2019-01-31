from django.test import TestCase

from adock.accounts import factories as accounts_factories

from .. import models
from .. import factories


class CarrierOnwerTestCase(TestCase):
    def test_model(self):
        carrier = factories.CarrierFactory()
        user = accounts_factories.UserFactory()
        self.assertEqual(carrier.owners.count(), 0)

        owner = models.CarrierUser.objects.create(carrier=carrier, user=user)
        self.assertEqual(carrier.owners.count(), 1)
        self.assertIsNotNone(owner.created_at)
