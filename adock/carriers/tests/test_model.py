from django.test import TestCase

from adock.accounts import models as accounts_models

from . import test
from .. import factories


class CarrierModelTestCase(TestCase):
    def test_get_siren_nic(self):
        carrier = factories.CarrierFactory(siret=test.VALID_SIRET)
        self.assertEqual(str(carrier), test.VALID_SIRET)
        self.assertEqual(carrier.get_siren(), "123456789")
        self.assertEqual(carrier.get_nic(), "12345")
        self.assertIn(test.VALID_SIRET, carrier.get_absolute_url())

    def test_enseigne_unaccent(self):
        carrier = factories.CarrierFactory(raison_sociale="DÉMÉNAGEURS MALADROITS")
        self.assertEqual(carrier.enseigne_unaccent, "DEMENAGEURS MALADROITS")


class CarrierExtendModelTestCase(TestCase):
    def test_create(self):
        carrier_editable = factories.CarrierEditableFactory()
        owner = accounts_models.User.objects.get()
        self.assertEqual(carrier_editable.created_by, owner)
