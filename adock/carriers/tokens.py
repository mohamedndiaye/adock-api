from django.contrib.auth.tokens import PasswordResetTokenGenerator


class CarrierEditableTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, carrier_editable, timestamp):  # pylint: disable=W0221
        # Valid for a carrier, an existing editable to replace and an carrier
        # editable to use and not yet applied.
        return "%s%s%s%s" % (
            carrier_editable.carrier.editable.pk,
            carrier_editable.pk,
            carrier_editable.confirmed_at or "",
            timestamp,
        )


carrier_editable_token = CarrierEditableTokenGenerator()
