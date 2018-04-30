from django.core.exceptions import ValidationError
from django.test import TestCase

from .. import factories
from . import test


class TransporteurModelTestCase(TestCase):
    def test_validators_too_short(self):
        transporteur = factories.TransporteurFactory(siret='1234567891234')
        with self.assertRaises(ValidationError) as cm:
            transporteur.full_clean()

        messages = cm.exception.message_dict
        self.assertEqual(messages['siret'][0], "1234567891234 n'est pas un numéro SIRET valide")

    def test_validators_not_digit(self):
        transporteur = factories.TransporteurFactory(siret='1A345678912345')

        with self.assertRaises(ValidationError):
            transporteur.full_clean()

    def test_get_siren_nic(self):
        transporteur = factories.TransporteurFactory(siret=test.VALID_SIRET)
        self.assertEqual(str(transporteur), test.VALID_SIRET)
        self.assertEqual(transporteur.get_siren(), '123456789')
        self.assertEqual(transporteur.get_nic(), '12345')
        self.assertIn(test.VALID_SIRET, transporteur.get_absolute_url())
