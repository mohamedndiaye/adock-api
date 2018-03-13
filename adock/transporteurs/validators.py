from django.core.exceptions import ValidationError

SIREN_LENGTH = 9
NIC_LENGTH = 5
SIRET_LENGTH = SIREN_LENGTH + NIC_LENGTH

def validate_administrative_number(value, length, name):
    if len(value) != length:
        raise ValidationError(
            "%(value)s n'est pas un numéro %(name)s valide",
            params={'value': value, 'name': name},
        )

def validate_siren(value):
    validate_administrative_number(value, SIREN_LENGTH, 'SIREN')

def validate_nic(value):
    validate_administrative_number(value, NIC_LENGTH, 'NIC')

def validate_siret(value):
    validate_administrative_number(value, SIRET_LENGTH, 'SIRET')
