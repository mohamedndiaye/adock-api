from django.core.exceptions import ValidationError
from django.test import TestCase

from . import factories

class TransporteurTestCase(TestCase):

    def test_save(self):
        transporteur = factories.TransporteurFactory(siren='123456789', nic='12345')
        self.assertEqual(transporteur.siret, '12345678912345')

    def test_validators(self):
        transporteur = factories.TransporteurFactory(siren='12345678', nic='123')
        with self.assertRaises(ValidationError) as cm:
            transporteur.full_clean()

        messages = cm.exception.message_dict
        self.assertEqual(messages['siren'][0], "12345678 n'est pas un numéro SIREN valide")
        self.assertEqual(messages['nic'][0], "123 n'est pas un numéro NIC valide")

    def test_vat_number(self):
        transporteur = factories.TransporteurFactory(siren='750017097', nic='00015')
        self.assertEqual(transporteur.get_vat_number(), 'FR18750017097')
