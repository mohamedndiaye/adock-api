from django.db import models


class Carrier(models.Model):
    siret = models.CharField(max_length=15, db_index=True, unique=True, editable=False)
    siren = models.CharField(max_length=9, db_index=True, editable=False)
    nic = models.CharField(max_length=5, editable=False)
    phone = models.CharField(max_length=10)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.siret

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.siret = self.siren + self.nic

        super().save(*args, **kwargs)
