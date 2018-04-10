import datetime

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from . import models as meta_models


class MetaTestCase(TestCase):

    def test_meta_index(self):
        today_iso = str(datetime.date.today())
        meta_models.Meta.objects.create(
            name='transporteur',
            data={'count': 42, 'date': today_iso}
        )
        response = self.client.get(reverse('meta'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['choices']['WORKING_AREA_CHOICES']['FRANCE'], 'France')
        self.assertEqual(data['choices']['SPECIALITY_CHOICES']['LOT'], 'Transport de lots')
        self.assertEqual(data['version'], settings.VERSION)
        self.assertEqual(data['transporteur']['count'], 42)
        self.assertEqual(data['transporteur']['date'], today_iso)
