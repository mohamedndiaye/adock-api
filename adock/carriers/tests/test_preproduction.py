from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings

from .. import factories, mails


class PreproductionTestCase(TestCase):
    def mail_carrier_editable_to_confirm(self, carrier_editable):
        new_carrier_editable = factories.CarrierEditableFactory(
            carrier=carrier_editable.carrier, email=carrier_editable.email
        )
        mails.mail_carrier_editable_to_confirm(
            ["description"], carrier_editable, new_carrier_editable
        )
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    @override_settings(PREPRODUCTION=False)
    def test_mail_to_carrier(self):
        carrier = factories.CarrierFactory(with_editable=True)
        mail_sent = self.mail_carrier_editable_to_confirm(carrier.editable)
        self.assertEqual(mail_sent.recipients(), [carrier.editable.email])

    @override_settings(PREPRODUCTION=True)
    def test_mail_to_carrier_preproduction(self):
        carrier = factories.CarrierFactory(with_editable=True)
        mail_sent = self.mail_carrier_editable_to_confirm(carrier.editable)
        self.assertEqual(
            mail_sent.recipients(), [email for (name, email) in settings.MANAGERS]
        )
