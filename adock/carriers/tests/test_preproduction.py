from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from .. import factories, mails


class PreproductionTestCase(TestCase):
    def get_mail_carrier_to_confirm_email(self, carrier):
        mails.mail_carrier_to_confirm_email(carrier, "http")
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    def get_mail_carrier_edit_code(self, carrier):
        mails.mail_carrier_edit_code(carrier)
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    @override_settings(PREPRODUCTION=False)
    def test_mail_to_carrier(self):
        carrier = factories.CarrierFactory(edit_code_at=timezone.now())
        mail_sent = self.get_mail_carrier_to_confirm_email(carrier)
        self.assertEqual(mail_sent.recipients(), [carrier.email])
        mail.outbox = []
        mail_sent = self.get_mail_carrier_edit_code(carrier)
        self.assertEqual(mail_sent.recipients(), [carrier.email])

    @override_settings(PREPRODUCTION=True)
    def test_mail_to_carrier_preproduction(self):
        carrier = factories.CarrierFactory(edit_code_at=timezone.now())
        mail_sent = self.get_mail_carrier_to_confirm_email(carrier)
        self.assertEqual(
            mail_sent.recipients(), [email for (name, email) in settings.MANAGERS]
        )
        mail.outbox = []
        mail_sent = self.get_mail_carrier_edit_code(carrier)
        self.assertEqual(
            mail_sent.recipients(), [email for (name, email) in settings.MANAGERS]
        )
