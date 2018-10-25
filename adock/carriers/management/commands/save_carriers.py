from django.core.management.base import BaseCommand
from django.db.utils import DatabaseError

from adock.carriers import models as carriers_models


class Command(BaseCommand):
    help = "Loop over the carriers to save them. Easy way to validate them."

    def handle(self, *args, **options):
        """
        When an error is detected on fetching, the algo fallbacks to one by one
        fetching to find the culprit.
        """
        count_ok = 0
        count_error = 0
        self.stdout.write("Fetch all carriers for saving.")
        try:
            for carrier in carriers_models.Carrier.objects.iterator():
                carrier.save()
                count_ok += 1
        except DatabaseError:
            self.stdout.write(
                self.style.WARNING(
                    "Fallback to check DB data, each model is fetched one by one by the ORM so be patient..."
                )
            )
            for carrier_siret in carriers_models.Carrier.objects.values_list(
                "siret", flat=True
            ):
                try:
                    carrier = carriers_models.Carrier.objects.get(pk=carrier_siret)
                except carriers_models.Carrier.DoesNotExist:
                    self.stderr.write(
                        self.style.WARNING("Unable to get '%s'") % carrier_siret
                    )
                    self.stderr.write(self.style.ERROR("%s") % e)
                    count_error += 1
                    continue

                try:
                    carrier.save()
                    count_ok += 1
                except DatabaseError as e:
                    self.stderr.write(
                        self.style.WARNING("Unable to save '%s'") % carrier
                    )
                    self.stderr.write(self.style.ERROR("%s") % e)
                    count_error += 1

        self.stdout.write(self.style.SUCCESS("Carriers saved: %d" % count_ok))
        self.stdout.write(self.style.ERROR("Carriers to fix: %d" % count_error))
