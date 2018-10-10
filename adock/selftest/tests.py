from django.urls import reverse

from ..accounts.test import AuthTestCase


class SelftestTestCase(AuthTestCase):

    def test_selftest(self):
        # Inception!
        url = reverse('selftest')
        response = self.client.get(url)
        self.assertContains(response, "Selftest page")
