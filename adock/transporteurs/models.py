from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.urls import reverse
from django.conf import settings

from phonenumber_field.modelfields import PhoneNumberField

from . import validators as transporteurs_validators

COMPLETENESS_PERCENT_MAX = 100
COMPLETENESS_PERCENT_MIN = 40

# Tied to completeness() property
EARNED_POINTS_MAX = 4
EARNED_POINT_VALUE = (COMPLETENESS_PERCENT_MAX - COMPLETENESS_PERCENT_MIN) / EARNED_POINTS_MAX

WORKING_AREA_UNDEFINED = ''
WORKING_AREA_INTERNATIONAL = 'INTERNATIONAL'
WORKING_AREA_FRANCE = 'FRANCE'
WORKING_AREA_DEPARTEMENT = 'DEPARTEMENT'
WORKING_AREA_CHOICES = (
    (WORKING_AREA_UNDEFINED, 'Non définie'),
    (WORKING_AREA_INTERNATIONAL, 'Internationale'),
    (WORKING_AREA_FRANCE, 'France'),
    (WORKING_AREA_DEPARTEMENT, 'Départementale')
)

SPECIALITY_CHOICES = (
    ('LOT', 'Transport de lots'),
    ('PALETTE', 'Palettes / Messagerie palettisée'),
    ('URBAIN', 'Urbain / Dernier kilomètre'),
    ('VRAC_SOLIDE', 'Vrac solide'),
    ('VRAC_LIQUIDE', 'Vrac liquide'),
    ('TEMPERATURE', 'Température dirigée'),
    ('PLATEAU', 'Plateau bachés et spécifiques'),
    ('MULTIMODAL', 'Multimodal'),
    ('LOCATION', 'Location'),
    ('ANIMAL', 'Animaux vivants'),
    ('VEHICULE', 'Transport de véhicules'),
    ('AUTRE', 'Autre')
)

class Transporteur(models.Model):
    siret = models.CharField(max_length=transporteurs_validators.SIRET_LENGTH,
        primary_key=True, db_index=True, editable=False)
    # nomen_long from Sirene (raison_sociale in Registre)
    # Always in uppercase
    raison_sociale = models.CharField(max_length=131)
    # Business name (filled with raison_sociale when undefined)
    enseigne = models.CharField(max_length=131)
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
    # depet from Sirene - Departement of the siege social
    departement = models.CharField(max_length=3, blank=True, null=False, default='')
    # telephone from GRECO used as default (changed)
    telephone = PhoneNumberField()
    # mail from GRECO used as default (changed)
    email = models.EmailField(blank=True, default='')
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
    lti_numero = models.CharField(max_length=16, blank=True, default='')
    lti_date_debut = models.DateField(blank=True, null=True)
    lti_date_fin = models.DateField(blank=True, null=True)
    lti_nombre = models.PositiveSmallIntegerField(default=0)
    # LC Licence communautaire => + de 3,5 tonnes
    lc_numero = models.CharField(max_length=16, blank=True, default='')
    lc_date_debut = models.DateField(blank=True, null=True)
    lc_date_fin = models.DateField(blank=True, null=True)
    lc_nombre = models.PositiveSmallIntegerField(default=0)
    # To store computed vat_number (computed by PostgreSQL on import)
    numero_tva = models.CharField(max_length=13, blank=True, null=True)
    working_area = models.CharField(
        max_length=15, choices=WORKING_AREA_CHOICES, blank=True, default=WORKING_AREA_UNDEFINED
    )
    # This field is used when working_area is set to WORKING_AREA_DEPARTEMENT
    # The default value is the departement of the company
    # Ex. 44, 2A, 976
    working_area_departements = ArrayField(
        models.CharField(max_length=3),
        blank=True, null=True,
        validators=[transporteurs_validators.validate_french_departement]
    )
    specialities = ArrayField(
        models.CharField(max_length=63, choices=SPECIALITY_CHOICES),
        blank=True, null=True
    )
    website = models.URLField(blank=True)
    # Filled by the user to describe his activity
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    # The field is updated when the form is submitted by the user.
    # It means a user has validated the information.
    validated_at = models.DateTimeField(blank=True, null=True)
    # Level of completeness of the carrier profile in percent
    completeness = models.PositiveSmallIntegerField(default=COMPLETENESS_PERCENT_MIN)
    in_sirene = models.BooleanField(
        default=False,
        help_text="Drapeau indiquant la présence de l'entreprise dans la base de données Sirène."
    )
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'transporteur'
        indexes = [
            models.Index(
                name='transporteur_search_order_by',
                fields=['enseigne', '-completeness']
            )
        ]
        # Take care to create the index, GinIndex is not able to handle it.
        # One solution is to inherit and adapt the code for that but it's not trivial
        # so the index is created in a raw SQL migration (0004 and updated in 0025).
        # CREATE INDEX transporteur_search_trgm_enseigne ON transporteur USING GIN (enseigne GIN_TRGM_OPS);

    def __str__(self):
        return self.siret

    def get_siren(self):
        return self.siret[:transporteurs_validators.SIREN_LENGTH]

    def get_nic(self):
        return self.siret[transporteurs_validators.SIREN_LENGTH:]

    def get_absolute_url(self):
        return reverse('transporteurs_detail', args=[self.siret])

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

    def save(self, *args, **kwargs):
        self.completeness = self.compute_completeness()
        if 'update_fields' in kwargs:
            # Could be a dict_keys instance so cast as list and be add 'completeness'
            kwargs['update_fields'] = list(kwargs['update_fields']) + ['completeness']
        super().save(*args, **kwargs)


class TransporteurLog(models.Model):
    transporteur = models.ForeignKey(Transporteur, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    # Contains the previous data of the instance
    data = JSONField()

    class Meta:
        db_table = 'transporteur_log'


class TransporteurFeed(models.Model):
    """The table Transporteur is fed by various sources (Sirène, Registre ou GRECO)"""
    source = models.CharField(max_length=32)
    title = models.CharField(max_length=126)
    url = models.URLField()
    filename = models.FilePathField(path=settings.DATAFILES_ROOT)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'transporteur_feed'
