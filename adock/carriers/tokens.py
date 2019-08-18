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


carrier_editable_token_generator = CarrierEditableTokenGenerator()


class CertificateTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, certificate, timestamp):  # pylint: disable=W0221
        # Ensure no others certificates have been confirmed in the meantime
        current_certificate = certificate.carrier.get_latest_certificate()
        current_certificate_pk = current_certificate.pk if current_certificate else None
        return "%s%s%s%s" % (
            current_certificate_pk,
            certificate.pk,
            certificate.confirmed_at or "",
            timestamp,
        )


certificate_token_generator = CertificateTokenGenerator()


class LicenseRenewalTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, license_renewal, timestamp):  # pylint: disable=W0221
        # Ensure not others have been confirmed in the meantime
        current_license_renewal = license_renewal.carrier.get_latest_certificate()
        current_certificate_pk = (
            current_license_renewal.pk if current_license_renewal else None
        )
        return "%s%s%s%s" % (
            current_certificate_pk,
            license_renewal.pk,
            license_renewal.confirmed_at or "",
            timestamp,
        )


license_renewal_token_generator = LicenseRenewalTokenGenerator()
