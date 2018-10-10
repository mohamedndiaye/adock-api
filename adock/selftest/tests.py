from django.test import TestCase
from django.urls import reverse


class SelftestTestCase(TestCase):

    def test_selftest(self):
        # Inception!
        url = reverse('selftest')
        response = self.client.get(url)
        self.assertContains(response, "Selftest page")
