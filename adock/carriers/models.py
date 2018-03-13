from django.db import models


class Carrier(models.Model):
    siret = models.CharField(max_length=15, db_index=True, unique=True, editable=False)
    phone = models.CharField(max_length=10)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.siret
