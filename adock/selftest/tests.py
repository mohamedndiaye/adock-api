from django.urls import reverse

from ..accounts.test import AuthTestCaseBase


class SelftestTestCase(AuthTestCaseBase):
    def test_selftest(self):
        url = reverse("selftest")
        response = self.client.get(
            url,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.http_authorization,
        )
        self.assertContains(response, "Selftest page")
