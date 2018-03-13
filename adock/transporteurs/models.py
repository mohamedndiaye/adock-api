from django.db import models

from . import validators as transporteurs_validators


class Transporteur(models.Model):
    siret = models.CharField(max_length=transporteurs_validators.SIRET_LENGTH,
        db_index=True, unique=True, editable=False)
    siren = models.CharField(max_length=transporteurs_validators.SIREN_LENGTH,
        db_index=True, editable=False,
        validators=[transporteurs_validators.validate_siren])
    nic = models.CharField(max_length=transporteurs_validators.NIC_LENGTH,
        editable=False,
        validators=[transporteurs_validators.validate_nic])
    # raison_sociale in GRECO and enseigne ou l1_normalisee in Sirene
    raison_sociale = models.CharField(max_length=38)
    # localisation in GRECO
    # numvoie, typevoie, libvoie in Sirene
    adresse = models.TextField()
    # code_postal in GRECO and codpos in Sirene
    code_postal = models.CharField(max_length=5)
    #
    # telephone in GRECO used as default (changed)
    telephone = models.CharField(max_length=10, blank=True)
    # mail in GRECO used as default (changed)
    email = models.EmailField(blank=True)
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

    def save(self, *args, **kwargs):
        if not self.pk:
            self.siret = self.siren + self.nic
        super().save(*args, **kwargs)

    def get_vat_number(self):
        key = (12 + 3 * (int(self.siren) % 97)) % 97
        return 'FR%d%s' % (key, self.siren)
