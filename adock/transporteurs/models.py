from django.db import models

from . import validators as transporteurs_validators


class Transporteur(models.Model):
    siret = models.CharField(max_length=transporteurs_validators.SIRET_LENGTH,
        validators=[transporteurs_validators.validate_siret],
        db_index=True, unique=True, editable=False)
    # raison_sociale in GRECO and enseigne ou l1_normalisee in Sirene
    raison_sociale = models.CharField(max_length=38)
    # localisation in GRECO
    # numvoie, typevoie, libvoie in Sirene
    adresse = models.CharField(max_length=126)
    # code_postal in GRECO and codpos in Sirene
    code_postal = models.CharField(max_length=5)
    #
    # telephone in GRECO used as default (changed)
    telephone = models.CharField(max_length=63, blank=True, default='')
    # mail in GRECO used as default (changed)
    email = models.EmailField(blank=True, default='')
    # dcret from Sirene
    date_creation = models.DateField()
    # ddebact from Sirene
    debut_activite = models.DateField()
    code_ape = models.CharField(max_length=5)
    libelle_ape = models.CharField(max_length=65)
    # TODO licenses (type + number)
    # license_total (DN)
    # is_above_3500_kg
    # working_area (FRANCE or DEPARTEMENT)
    # working_area_departments = array of zip code
    # type_marchandise = categories from FNTR
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.siret

    def get_siren(self):
        return self.siret[:transporteurs_validators.SIREN_LENGTH]

    def get_nic(self):
        return self.siret[transporteurs_validators.SIREN_LENGTH:]

    def get_vat_number(self):
        siren = self.get_siren()
        key = (12 + 3 * (int(siren) % 97)) % 97
        return 'FR%d%s' % (key, siren)
