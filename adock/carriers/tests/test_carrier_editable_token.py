from django.urls import reverse
from django.utils import timezone

from . import test
from .. import factories, tokens


class CarrierEmailConfirmationTestCase(test.CarrierTestCaseMixin):
    def setUp(self):
        self.carrier = factories.CarrierFactory(with_editable=True)
        self.carrier_detail_url = reverse(
            "carriers_detail", kwargs={"carrier_siret": self.carrier.siret}
        )

    def test_idempotent(self):
        token = tokens.carrier_editable_token_generator.make_token(
            self.carrier.editable
        )
        self.assertIsNotNone(token)
        self.assertNotEqual(token, "")
        same_token = tokens.carrier_editable_token_generator.make_token(
            self.carrier.editable
        )
        self.assertEqual(token, same_token)

    def test_another_applied_editable(self):
        old_token = tokens.carrier_editable_token_generator.make_token(
            self.carrier.editable
        )
        self.carrier.editable.pk += 1
        new_token = tokens.carrier_editable_token_generator.make_token(
            self.carrier.editable
        )
        self.assertNotEqual(old_token, new_token)

    def test_already_confirmed(self):
        old_token = tokens.carrier_editable_token_generator.make_token(
            self.carrier.editable
        )
        self.carrier.editable.confirmed_at = timezone.now()
        new_token = tokens.carrier_editable_token_generator.make_token(
            self.carrier.editable
        )
        self.assertNotEqual(old_token, new_token)

    def test_altered_token(self):
        token = tokens.carrier_editable_token_generator.make_token(
            self.carrier.editable
        )
        url = reverse(
            "carriers_carrier_editable_confirm",
            kwargs={
                "carrier_editable_id": self.carrier.editable.pk,
                "token": token + "z",
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
