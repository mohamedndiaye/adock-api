from django.db import models

from . import validators as carriers_validators


class Carrier(models.Model):
    siret = models.CharField(max_length=carriers_validators.SIRET_LENGTH,
        db_index=True, unique=True, editable=False)
    siren = models.CharField(max_length=carriers_validators.SIREN_LENGTH,
        db_index=True, editable=False,
        validators=[carriers_validators.validate_siren])
    nic = models.CharField(max_length=carriers_validators.NIC_LENGTH,
        editable=False,
        validators=[carriers_validators.validate_nic])
    phone = models.CharField(max_length=10, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.siret

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.siret = self.siren + self.nic

        super().save(*args, **kwargs)
