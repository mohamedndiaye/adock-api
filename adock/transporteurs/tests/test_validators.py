from django.test import TestCase

from ..validators import is_french_departement

class TransporteurValidatorsTestCase(TestCase):

    def test_french_departements(self):
        self.assertTrue(is_french_departement('2A'))
        self.assertFalse(is_french_departement('2C'))
        self.assertTrue(is_french_departement('44'))
        self.assertFalse(is_french_departement('440'))
        self.assertFalse(is_french_departement('20'))
        self.assertTrue(is_french_departement('974'))
        self.assertFalse(is_french_departement('-1'))
