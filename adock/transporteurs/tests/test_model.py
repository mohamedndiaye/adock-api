from django.test import TestCase

from . import test
from .. import factories


class TransporteurModelTestCase(TestCase):
    def test_get_siren_nic(self):
        transporteur = factories.TransporteurFactory(siret=test.VALID_SIRET)
        self.assertEqual(str(transporteur), test.VALID_SIRET)
        self.assertEqual(transporteur.get_siren(), "123456789")
        self.assertEqual(transporteur.get_nic(), "12345")
        self.assertIn(test.VALID_SIRET, transporteur.get_absolute_url())

    def test_enseigne_unaccent(self):
        transporteur = factories.TransporteurFactory(
            raison_sociale="DÉMÉNAGEURS MALADROITS"
        )
        self.assertEqual(transporteur.enseigne_unaccent, "DEMENAGEURS MALADROITS")
