from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models import Lookup
from django.db.models.fields import Field
from django.urls import reverse
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from adock.accounts import models as accounts_models

from . import validators as carriers_validators


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
    ("ANIMAL", "Animaux vivants"),
    ("AUTRE", "Autre"),
    ("BOIS", "Bois"),
    ("DECHETS", "Déchets"),
    ("DEMENAGEMENT", "Déménagement"),
    ("LOCATION", "Location"),
    ("LOT", "Lots"),
    ("MESSAGERIE", "Messagerie express"),
    ("MULTIMODAL", "Multimodal"),
    ("PALETTE", "Palettes / Messagerie palettisée"),
    ("PLATEAU", "Plateau bachés et spécifiques"),
    ("TEMPERATURE", "Température dirigée"),
    ("URBAIN", "Urbain / Dernier kilomètre"),
    ("VEHICULE", "Véhicules"),
    ("VRAC_LIQUIDE", "Vrac liquide"),
    ("VRAC_SOLIDE", "Vrac solide"),
)

OBJECTIF_CO2_ENLISTED = "ENLISTED"
OBJECTIF_CO2_LABELLED = "LABELLED"

OBJECTIF_CO2_CHOICES = (
    (OBJECTIF_CO2_ENLISTED, "Engagé"),
    (OBJECTIF_CO2_LABELLED, "Labellisé"),
)


class Carrier(models.Model):
    siret = models.CharField(
        max_length=carriers_validators.SIRET_LENGTH,
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
    # telephone from GRECO used as default (changed) but required in form
    telephone = PhoneNumberField(blank=True, default="")
    # mail from GRECO used as default (changed) but required in form
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
        validators=[carriers_validators.validate_french_departement],
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
        help_text="Date de la suppression de l'établissement de la base Sirene.",
    )
    objectif_co2 = models.CharField(
        max_length=8, choices=OBJECTIF_CO2_CHOICES, blank=True, null=False, default=""
    )
    objectif_co2_begin = models.DateField(blank=True, null=True)
    # Usually begin plus 3 years
    objectif_co2_end = models.DateField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    editable = models.ForeignKey(
        "CarrierEditable",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    owners = models.ManyToManyField(
        accounts_models.User, through="CarrierUser", related_name="carriers"
    )

    class Meta:
        db_table = "carrier"
        # Take care to create manual index because GinIndex is not able to
        # handle it. One solution is to inherit and adapt the code for that but
        # it's not trivial so the index is created in a raw SQL migration and
        # the required extension is installed by Ansible.

    def __str__(self):
        return self.siret

    def get_siren(self):
        return self.siret[: carriers_validators.SIREN_LENGTH]

    def get_nic(self):
        return self.siret[carriers_validators.SIREN_LENGTH :]

    def get_absolute_url(self):
        return reverse("carriers_detail", args=[self.siret])

    def compute_completeness(self):
        """
        Take care to adjust EARNED_POINTS_MAX on changes or unit tests will warn you!
        Rules:
        - nothing: 0
        - +0.5 for a phone or an email not validated
        - +1 for all others (phone, email, working_area and specialities)
        Maximum: 4
        """
        if not self.editable:
            return COMPLETENESS_PERCENT_MIN

        earned_points = 0

        if self.editable.telephone:
            earned_points += 1
        if self.editable.email:
            earned_points += 1
        if self.editable.working_area != WORKING_AREA_UNDEFINED:
            earned_points += 1
        if self.editable.specialities:
            earned_points += 1

        return COMPLETENESS_PERCENT_MIN + earned_points * EARNED_POINT_VALUE

    def lock(self):
        self.email_confirmed_at = timezone.now()
        self.save()

    def is_locked(self):
        # The email has been confirmed
        return bool(self.email_confirmed_at)

    def has_owner(self):
        return self.owners.exists()

    def add_owner(self, user):
        try:
            owner = self.owners.get(carrieruser__user=user)
        except accounts_models.User.DoesNotExist:
            owner = CarrierUser.objects.create(carrier=self, user=user)
        return owner

    def get_latest_certificate(self):
        try:
            return self.certificates.latest("created_at")
        except CarrierCertificate.DoesNotExist:
            return None

    def save(self, *args, **kwargs):  # pylint: disable=W0221
        self.completeness = self.compute_completeness()
        if "update_fields" in kwargs:
            # Could be a dict_keys instance so cast as list and add 'completeness'
            kwargs["update_fields"] = list(kwargs["update_fields"])
            kwargs["update_fields"].append("completeness")
        super().save(*args, **kwargs)


class CarrierEditable(models.Model):
    """Editable part of the carrier.
    The history of changes on carriers are set by the list of CarrierEditable.
    """

    carrier = models.ForeignKey(
        Carrier, on_delete=models.CASCADE, related_name="changes"
    )
    # FIXME Should we expose not validated phone?
    telephone = PhoneNumberField(blank=False, null=False)
    email = models.EmailField(blank=False, null=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        accounts_models.User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="carrier_changes",
    )
    confirmed_at = models.DateTimeField(blank=True, null=True)
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
        validators=[carriers_validators.validate_french_departement],
    )
    specialities = ArrayField(
        models.CharField(max_length=63, choices=SPECIALITY_CHOICES),
        blank=True,
        null=True,
    )
    website = models.URLField(blank=True)
    # Filled by the user to describe his activity
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "carrier_editable"
        get_latest_by = "pk"


class CarrierLog(models.Model):
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    # Contains the previous data of the instance
    data = JSONField()

    class Meta:
        db_table = "carrier_log"


class CarrierFeed(models.Model):
    """The table Carrier is fed by various sources (Sirene, Registre ou GRECO)"""

    source = models.CharField(max_length=32)
    title = models.CharField(max_length=126)
    url = models.URLField()
    filename = models.FileField()
    downloaded_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "carrier_feed"


CERTIFICATE_NO_WORKERS = "no-workers"
CERTIFICATE_WORKERS = "workers"
CERTIFICATE_CHOICES = (
    (CERTIFICATE_NO_WORKERS, "Attestation de non emploi de travailleurs étrangers"),
    (CERTIFICATE_WORKERS, "Attestation d'emploi de travailleurs étrangers"),
)
CERTIFICATE_DICT = dict(CERTIFICATE_CHOICES)


class CarrierCertificate(models.Model):
    carrier = models.ForeignKey(
        Carrier, on_delete=models.CASCADE, related_name="certificates"
    )
    kind = models.CharField(max_length=32, choices=CERTIFICATE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    data = JSONField()

    def __str__(self):
        return "%s: %s" % (self.carrier.siret, self.get_kind_display())

    class Meta:
        db_table = "carrier_certificate"


class CarrierUser(models.Model):
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE)
    user = models.ForeignKey(accounts_models.User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "carrier_user"
        unique_together = ("carrier", "user")
