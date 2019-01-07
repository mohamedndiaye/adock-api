from django.urls import reverse

from ..accounts.test import AuthTestCaseBase


class SelftestTestCase(AuthTestCaseBase):
    def test_selftest(self):
        http_authorization = self.log_in()
        url = reverse("selftest")
        response = self.client.get(
            url, content_type="application/json", HTTP_AUTHORIZATION=http_authorization
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Selftest page")
