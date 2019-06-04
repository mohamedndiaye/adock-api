import re

from django.core import validators
from django.core.exceptions import ValidationError

SIREN_LENGTH = 9
NIC_LENGTH = 5
SIRET_LENGTH = SIREN_LENGTH + NIC_LENGTH

RE_NOT_DIGIT_ONLY = re.compile(r"\D")


def is_french_departement(departement):
    if departement in ("2A", "2B"):
        return True

    try:
        departement_integer = int(departement)
    except ValueError:
        return False

    # Don't exist
    if departement_integer == 20:
        return False

    if 1 <= departement_integer <= 95 or 971 <= departement_integer <= 974:
        return True

    # 975 is not used
    if departement_integer == 976:
        return True

    return False


def validate_french_departement(departements):
    for departement in departements:
        if not is_french_departement(departement):
            raise ValidationError(
                "« %(value)s » n'est pas un département français valide.",
                params={"value": departement},
            )


def validate_scheme(value):
    if value and not value.startswith("http://") and not value.startswith("https://"):
        return "http://" + value

    return value


class LooseURLValidator(validators.URLValidator):
    def __call__(self, value):
        validate_scheme(value)
        return super().__call__(validate_scheme(value))
