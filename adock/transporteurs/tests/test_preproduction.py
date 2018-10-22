from django.core import mail
from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from .. import mails
from .. import factories


class PreproductionTestCase(TestCase):

    def get_mail_transporteur_to_confirm_email(self, transporteur):
        mails.mail_transporteur_to_confirm_email(transporteur, 'http')
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    def get_mail_transporteur_edit_code(self, transporteur):
        mails.mail_transporteur_edit_code(transporteur)
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    @override_settings(PREPRODUCTION=False)
    def test_mail_to_transporteur(self):
        transporteur = factories.TransporteurFactory(edit_code_at=timezone.now())
        mail_sent = self.get_mail_transporteur_to_confirm_email(transporteur)
        self.assertEqual(mail_sent.recipients(), [transporteur.email])
        mail.outbox = []
        mail_sent = self.get_mail_transporteur_edit_code(transporteur)
        self.assertEqual(mail_sent.recipients(), [transporteur.email])

    @override_settings(PREPRODUCTION=True)
    def test_mail_to_transporteur_preproduction(self):
        transporteur = factories.TransporteurFactory(edit_code_at=timezone.now())
        mail_sent = self.get_mail_transporteur_to_confirm_email(transporteur)
        self.assertEqual(mail_sent.recipients(), list(settings.MANAGERS))
        mail.outbox = []
        mail_sent = self.get_mail_transporteur_edit_code(transporteur)
        self.assertEqual(mail_sent.recipients(), list(settings.MANAGERS))
