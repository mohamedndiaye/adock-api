from django.test import TestCase

from . import models as carriers_models

class CarrierTestCase(TestCase):

    def test_carrier_save(self):
        carrier = carriers_models.Carrier.objects.create(siren='123456789', nic='12345')
        self.assertEqual(carrier.siret, '12345678912345')
