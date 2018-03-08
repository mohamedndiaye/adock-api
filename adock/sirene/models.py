from django.db import models

# The model is only used for testing purpose, the real table is created/populated via PostgreSQL
class Sirene(models.Model):
    siren = models.CharField(max_length=9)
    nic = models.CharField(max_length=5)
    l1_normalisee = models.CharField(max_length=38)

    class Meta:
        db_table = 'sirene'
