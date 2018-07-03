from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailConfirmationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, transporteur, timestamp):
        return '%s%s%s%s' % (
            transporteur.siret,
            transporteur.email,
            transporteur.email_confirmed_at or '',
            timestamp)


email_confirmation_token = EmailConfirmationTokenGenerator()
