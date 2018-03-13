from django.db import models

# The table is created/populated via PostgreSQL to speed up import

class Sirene(models.Model):
    siren = models.CharField(max_length=9)
    nic = models.CharField(max_length=5)
    l1_normalisee = models.CharField(max_length=38)

    def get_siret(self):
        return self.siren + self.nic

    class Meta:
        db_table = 'sirene'
