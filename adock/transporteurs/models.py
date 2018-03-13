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
    telephone = models.CharField(max_length=10, blank=True)
    email = models.EmailField(blank=True)
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
