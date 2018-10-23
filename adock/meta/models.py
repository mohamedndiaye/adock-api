from django.contrib.postgres.fields import JSONField
from django.db import models


class Meta(models.Model):
    """Convenient models to store very small and not structured information."""

    name = models.CharField(max_length=63, unique=True)
    data = JSONField()

    class Meta:
        db_table = "meta"

    def __str__(self):
        return self.name
