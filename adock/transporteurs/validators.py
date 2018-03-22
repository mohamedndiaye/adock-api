import re
from django.core.exceptions import ValidationError

SIREN_LENGTH = 9
NIC_LENGTH = 5
SIRET_LENGTH = SIREN_LENGTH + NIC_LENGTH

RE_NOT_DIGIT = re.compile(r'\D')

def validate_administrative_number(value, length, name):
    if len(value) != length or RE_NOT_DIGIT.search(value):
        raise ValidationError(
            "%(value)s n'est pas un numéro %(name)s valide",
            params={'value': value, 'name': name},
        )

def validate_siren(value):  # pragma: no cover - used in migration
    validate_administrative_number(value, SIREN_LENGTH, 'SIREN')

def validate_nic(value):  # pragma: no cover - used in migration
    validate_administrative_number(value, NIC_LENGTH, 'NIC')

def validate_siret(value):
    validate_administrative_number(value, SIRET_LENGTH, 'SIRET')
