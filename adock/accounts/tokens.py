from django.contrib.auth.tokens import PasswordResetTokenGenerator


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        login_timestamp = (
            ""
            if user.last_login is None
            else user.last_login.replace(microsecond=0, tzinfo=None)
        )
        # is_active will toggle on activation but I prefer to add
        # login_timestamp to be sure token will be invalid if the the is_active
        # boolean is False again.
        return (
            str(user.pk)
            + user.password
            + str(login_timestamp)
            + str(timestamp)
            + str(user.is_active)
        )


account_activation_token = TokenGenerator()
