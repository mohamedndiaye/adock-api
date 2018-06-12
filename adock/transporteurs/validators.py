import re

SIREN_LENGTH = 9
NIC_LENGTH = 5
SIRET_LENGTH = SIREN_LENGTH + NIC_LENGTH

RE_NOT_DIGIT = re.compile(r'\D')

def is_french_departement(departement):
    if departement in ('2A', '2B'):
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
