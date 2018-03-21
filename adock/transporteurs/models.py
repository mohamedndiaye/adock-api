from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from . import validators as transporteurs_validators

LICENCE_LCM = 'LCM'
LICENCE_LTIM = 'LTIM'
LICENCE_LCV = 'LCV'
LICENSE_LTIV = 'LTIV'

# LICENSE_CHOICES = (
#     (LICENCE_LCM, "Licence communautaire marchandise, camion > 3,5 tonnes"),
#     (LICENCE_LTIM, "Licence de transport intérieur de marchandise : VUL < 3,5 tonnes"),
#     # Not used
#     (LICENCE_LCV, "Licence communautaire voyageurs, car > 9 places"),
#     (LICENSE_LTIV, "Licence de transport intérieur de voyageurs : < 9 places."),
# )

COMPLETENESS_PERCENT_MAX = 100
COMPLETENESS_PERCENT_MIN = 40

# Tied to completeness() property
EARNED_POINTS_MAX = 4
EARNED_POINT_VALUE = (COMPLETENESS_PERCENT_MAX - COMPLETENESS_PERCENT_MIN) / EARNED_POINTS_MAX


class Transporteur(models.Model):
    siret = models.CharField(max_length=transporteurs_validators.SIRET_LENGTH,
        validators=[transporteurs_validators.validate_siret],
        db_index=True, unique=True, editable=False)
    # nomen_long from Sirene (raison_sociale in GRECO)
    raison_sociale = models.CharField(max_length=131)
    # numvoie, typevoie, libvoie from Sirene
    # (localisation in GRECO)
    adresse = models.CharField(max_length=126)
    # codpos from Sirene (code_postal in GRECO)
    code_postal = models.CharField(max_length=5)
    # libcom from Sirene
    ville = models.CharField(max_length=32)
    # telephone from GRECO used as default (changed)
    telephone = PhoneNumberField()
    # mail from GRECO used as default (changed)
    email = models.EmailField(blank=True, default='')
    # dcret from Sirene (inscription_activite from GRECO)
    date_creation = models.DateField()
    # ddebact from Sirene
    debut_activite = models.DateField()
    # apen700 from Sirene
    code_ape = models.CharField(max_length=5)
    # libapen from Sirene
    libelle_ape = models.CharField(max_length=65)
    # Licenses for <3.5 tons
    lower_than_3_5_licenses = models.IntegerField(default=0)
    # Licenses for >3.5 tons
    greater_than_3_5_licenses = models.IntegerField(default=0)
    # To store computed vat_number
    numero_tva = models.CharField(max_length=13)
    # working_area (FRANCE or DEPARTEMENT)
    # working_area_departments = array of zip code
    # type_marchandise = categories from FNTR
    created_at = models.DateTimeField(auto_now_add=True)
    # The field is updated when the form is submitted by the user.
    # It means a user has validated the information.
    validated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.siret

    def get_siren(self):
        return self.siret[:transporteurs_validators.SIREN_LENGTH]

    def get_nic(self):
        return self.siret[transporteurs_validators.SIREN_LENGTH:]

    @property
    def completeness(self):
        # Take care to adjust EARNED_POINTS_MAX on changes or unit tests will warn you!
        earned_points = 0
        original_fields_weight = 1 if self.validated_at is None else 2
        if self.telephone:
            earned_points += original_fields_weight
        if self.email:
            earned_points += original_fields_weight

        return COMPLETENESS_PERCENT_MIN + EARNED_POINT_VALUE * earned_points
