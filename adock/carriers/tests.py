from django.core.exceptions import ValidationError
from django.test import TestCase

from . import models as carriers_models

class CarrierTestCase(TestCase):

    def test_save(self):
        carrier = carriers_models.Carrier.objects.create(siren='123456789', nic='12345')
        self.assertEqual(carrier.siret, '12345678912345')

    def test_validators(self):
        carrier = carriers_models.Carrier.objects.create(siren='12345678', nic='123')
        with self.assertRaises(ValidationError) as cm:
            carrier.full_clean()

        messages = cm.exception.message_dict
        self.assertEqual(messages['siren'][0], '12345678 is not a valid SIREN number')
        self.assertEqual(messages['nic'][0], '123 is not a valid NIC number')
