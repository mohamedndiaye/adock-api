from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.validators import EmailValidator

from adock.carriers import models as carriers_models


class Command(BaseCommand):
    help = "Validate all emails in DB."

    def handle(self, *args, **options):
        carriers = carriers_models.Carrier.objects.exclude(email="")
        email_validator = EmailValidator()
        for carrier in carriers:
            try:
                email_validator(carrier.email)
            except ValidationError:
                new_email = input("%s:\n" % carrier.email)
                carrier.email = new_email
                carrier.save()
