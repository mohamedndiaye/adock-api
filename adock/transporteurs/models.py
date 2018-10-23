import random

from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models import Lookup
from django.db.models.fields import Field
from django.urls import reverse
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from . import validators as transporteurs_validators


@Field.register_lookup
class UnaccentContains(Lookup):
    lookup_name = "ucontains"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        esc_rhs = r"REPLACE(REPLACE(REPLACE({}, '\', '\\'), '%%', '\%%'), '_', '\_')".format(
            rhs
        )
        return "{} LIKE '%%' || UNACCENT({}) || '%%'".format(lhs, esc_rhs), params


COMPLETENESS_PERCENT_MAX = 100
COMPLETENESS_PERCENT_MIN = 40

# Tied to completeness() property
EARNED_POINTS_MAX = 4
EARNED_POINT_VALUE = (
    COMPLETENESS_PERCENT_MAX - COMPLETENESS_PERCENT_MIN
) / EARNED_POINTS_MAX

WORKING_AREA_UNDEFINED = ""
WORKING_AREA_INTERNATIONAL = "INTERNATIONAL"
WORKING_AREA_FRANCE = "FRANCE"
WORKING_AREA_REGION = "REGION"
WORKING_AREA_DEPARTEMENT = "DEPARTEMENT"
WORKING_AREA_CHOICES = (
    (WORKING_AREA_UNDEFINED, "Non définie"),
    (WORKING_AREA_INTERNATIONAL, "Internationale"),
    (WORKING_AREA_FRANCE, "France"),
    (WORKING_AREA_REGION, "Régionale"),
    (WORKING_AREA_DEPARTEMENT, "Départementale"),
)

SPECIALITY_CHOICES = (
    ("LOT", "Transport de lots"),
    ("PALETTE", "Palettes / Messagerie palettisée"),
    ("URBAIN", "Urbain / Dernier kilomètre"),
    ("VRAC_SOLIDE", "Vrac solide"),
    ("VRAC_LIQUIDE", "Vrac liquide"),
    ("TEMPERATURE", "Température dirigée"),
    ("PLATEAU", "Plateau bachés et spécifiques"),
    ("MESSAGERIE", "Messagerie express"),
    ("MULTIMODAL", "Multimodal"),
    ("LOCATION", "Location"),
    ("ANIMAL", "Animaux vivants"),
    ("VEHICULE", "Transport de véhicules"),
    ("AUTRE", "Autre"),
)

OBJECTIF_CO2_ENLISTED = "ENLISTED"
OBJECTIF_CO2_LABELLED = "LABELLED"

OBJECTIF_CO2_CHOICES = (
    (OBJECTIF_CO2_ENLISTED, "Engagé"),
    (OBJECTIF_CO2_LABELLED, "Labellisé"),
)


class Transporteur(models.Model):
    siret = models.CharField(
        max_length=transporteurs_validators.SIRET_LENGTH,
        primary_key=True,
        db_index=True,
        editable=False,
    )
    # nomen_long from Sirene (raison_sociale in Registre)
    # Always in uppercase
    raison_sociale = models.CharField(max_length=131)
    # Business name (filled with raison_sociale when undefined)
    enseigne = models.CharField(max_length=131)
    # Only < 1% of entries use accents but to include them in results w/o
    # performance penality we create a field with a variant of enseigne w/o
    # accents. Dynamic use of 'unaccent' is too slow.
    enseigne_unaccent = models.CharField(max_length=131)
    # from Registre
    categorie_juridique = models.TextField()
    # This company is the siege social
    is_siege = models.BooleanField(default=False)
    # numvoie, typvoie, libvoie from Sirene
    adresse = models.CharField(max_length=126)
    # codpos from Sirene (code_postal in Registre)
    code_postal = models.CharField(max_length=5)
    # libcom from Sirene (commune in Registre)
    ville = models.CharField(max_length=32)
    # code_departement from Registre
    departement = models.CharField(max_length=3, blank=True, null=False, default="")
    # telephone from GRECO used as default (changed)
    telephone = PhoneNumberField(blank=True, default="")
    # mail from GRECO used as default (changed)
    email = models.EmailField(blank=True, default="")
    # Set when the user clicks on the provided URL with one time token and to
    # None when the email is modified.
    email_confirmed_at = models.DateTimeField(blank=True, null=True)
    # dcret from Sirene (inscription_activite from GRECO).
    # Can be null (not present in Sirene)
    date_creation = models.DateField(blank=True, null=True)
    # ddebact from Sirene
    debut_activite = models.DateField(blank=True, null=True)
    # apen700 from Sirene
    code_ape = models.CharField(max_length=5)
    # libapen from Sirene
    libelle_ape = models.CharField(max_length=65)
    # Name of the transport manager
    gestionnaire = models.CharField(max_length=131)
    # LTI Licence de transport intérieur => - de 3,5 tonnes
    # LTIM and LCM in GRECO
    # LTI 'YYYY RR NNNNNNNN', YYYY year, RR region, number starting to one of current year
    lti_numero = models.CharField(max_length=16, blank=True, default="")
    lti_date_debut = models.DateField(blank=True, null=True)
    lti_date_fin = models.DateField(blank=True, null=True)
    lti_nombre = models.PositiveSmallIntegerField(default=0)
    # LC Licence communautaire => + de 3,5 tonnes
    lc_numero = models.CharField(max_length=16, blank=True, default="")
    lc_date_debut = models.DateField(blank=True, null=True)
    lc_date_fin = models.DateField(blank=True, null=True)
    lc_nombre = models.PositiveSmallIntegerField(default=0)
    # To store computed vat_number (computed by PostgreSQL on import)
    numero_tva = models.CharField(max_length=13, blank=True, null=True)
    working_area = models.CharField(
        max_length=15,
        choices=WORKING_AREA_CHOICES,
        blank=True,
        default=WORKING_AREA_UNDEFINED,
    )
    # This field is used when working_area is set to WORKING_AREA_DEPARTEMENT
    # The default value is the departement of the company
    # Ex. 44, 2A, 976
    working_area_departements = ArrayField(
        models.CharField(max_length=3),
        blank=True,
        null=True,
        validators=[transporteurs_validators.validate_french_departement],
    )
    specialities = ArrayField(
        models.CharField(max_length=63, choices=SPECIALITY_CHOICES),
        blank=True,
        null=True,
    )
    website = models.URLField(blank=True)
    # Filled by the user to describe his activity
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    # The field is updated when the form is submitted by the user.
    # It means a user has validated the information.
    validated_at = models.DateTimeField(blank=True, null=True)
    # Level of completeness of the carrier profile in percent
    completeness = models.PositiveSmallIntegerField(default=COMPLETENESS_PERCENT_MIN)
    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date de la supression de l'établissement du registre des transports.",
    )
    sirene_deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date de la suppression de l'établissement de la base Sirène.",
    )
    edit_code = models.IntegerField(blank=True, null=True)
    edit_code_at = models.DateTimeField(blank=True, null=True)
    objectif_co2 = models.CharField(
        max_length=8, choices=OBJECTIF_CO2_CHOICES, blank=True, null=False, default=""
    )
    objectif_co2_begin = models.DateField(blank=True, null=True)
    # Usually begin plus 3 years
    objectif_co2_end = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "transporteur"
        # Take care to create manual index because GinIndex is not able to
        # handle it. One solution is to inherit and adapt the code for that but
        # it's not trivial so the index is created in a raw SQL migration and
        # the required extension is installed by Ansible.

    def __str__(self):
        return self.siret

    def get_siren(self):
        return self.siret[: transporteurs_validators.SIREN_LENGTH]

    def get_nic(self):
        return self.siret[transporteurs_validators.SIREN_LENGTH :]

    def get_absolute_url(self):
        return reverse("transporteurs_detail", args=[self.siret])

    def compute_completeness(self):
        """
        Take care to adjust EARNED_POINTS_MAX on changes or unit tests will warn you!
        Rules:
        - nothing: 0
        - +0.5 for a phone or an email not validated
        - +1 for all others (phone, email, working_area and specialities)
        Maximum: 4
        """
        earned_points = 0
        original_fields_weight = 0.5 if self.validated_at is None else 1
        if self.telephone:
            earned_points += original_fields_weight
        if self.email:
            earned_points += original_fields_weight
        if self.working_area != WORKING_AREA_UNDEFINED:
            earned_points += 1
        if self.specialities:
            earned_points += 1

        return COMPLETENESS_PERCENT_MIN + earned_points * EARNED_POINT_VALUE

    def lock(self):
        self.email_confirmed_at = timezone.now()
        self.save()

    def is_locked(self):
        # The email has been confirmed
        return bool(self.email_confirmed_at)

    def get_edit_code_timeout_at(self):
        return self.edit_code_at + settings.TRANSPORTEUR_EDIT_CODE_INTERVAL

    def edit_code_has_expired(self):
        if not self.edit_code:
            # Unset is considered expired
            return True

        if self.get_edit_code_timeout_at() < timezone.now():
            # The stored edit code has expired
            return True

        return False

    def check_edit_code(self, edit_code):
        if not self.is_locked():
            # Access granted to not locked transporteur
            return True

        if self.edit_code_has_expired():
            # The current edit code is too old
            return False

        if not edit_code:
            # Wrong edit code
            return False

        try:
            edit_code = int(edit_code)
        except ValueError:
            return False

        if self.edit_code != edit_code:
            return False

        return True

    def set_edit_code(self):
        self.edit_code = random.randint(100000, 999999)
        self.edit_code_at = timezone.now()

    def save(self, *args, **kwargs):  # pylint: disable=W0221
        self.completeness = self.compute_completeness()
        if "update_fields" in kwargs:
            # Could be a dict_keys instance so cast as list and add 'completeness'
            kwargs["update_fields"] = list(kwargs["update_fields"])
            kwargs["update_fields"].append("completeness")
        super().save(*args, **kwargs)


class TransporteurLog(models.Model):
    transporteur = models.ForeignKey(Transporteur, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    # Contains the previous data of the instance
    data = JSONField()

    class Meta:
        db_table = "transporteur_log"


class TransporteurFeed(models.Model):
    """The table Transporteur is fed by various sources (Sirene, Registre ou GRECO)"""

    source = models.CharField(max_length=32)
    title = models.CharField(max_length=126)
    url = models.URLField()
    filename = models.FileField()
    downloaded_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "transporteur_feed"
