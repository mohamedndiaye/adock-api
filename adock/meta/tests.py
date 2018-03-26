from django.urls import reverse
from django.test import TestCase


class MetaTestCase(TestCase):

    def test_meta_index(self):
        response = self.client.get(reverse('meta'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['choices']['WORKING_AREA_CHOICES']['FRANCE'], 'France')
