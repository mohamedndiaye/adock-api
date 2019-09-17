from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings

from adock.accounts import factories as accounts_factories
from adock.carriers import factories as carriers_factories
from adock.carriers import mails as carriers_mails


class PreproductionTestCase(TestCase):
    def mail_carrier_editable_to_confirm(self, carrier_editable):
        user = accounts_factories.UserFactory()
        new_carrier_editable = carriers_factories.CarrierEditableFactory(
            carrier=carrier_editable.carrier,
            created_by=user,
            email=carrier_editable.email,
        )
        carriers_mails.mail_carrier_editable_to_confirm(
            ["description"], carrier_editable, new_carrier_editable
        )
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    @override_settings(ENVIRONMENT="PRODUCTION")
    def test_mail_to_carrier(self):
        carrier = carriers_factories.CarrierFactory(with_editable=True)
        mail_sent = self.mail_carrier_editable_to_confirm(carrier.editable)
        self.assertEqual(mail_sent.recipients(), [carrier.editable.email])

    @override_settings(ENVIRONMENT="PREPRODUCTION")
    def test_mail_to_carrier_preproduction(self):
        carrier = carriers_factories.CarrierFactory(with_editable=True)
        mail_sent = self.mail_carrier_editable_to_confirm(carrier.editable)
        self.assertEqual(
            mail_sent.recipients(), [email for (name, email) in settings.MANAGERS]
        )
