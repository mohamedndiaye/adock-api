from django.core.management.base import BaseCommand
from django.db.utils import DatabaseError

from adock.transporteurs import models as transporteurs_models


class Command(BaseCommand):
    help = "Loop over the transporteurs to save them. Easy way to validate them."

    def handle(self, *args, **options):
        """
        When an error is detected on fetching, the algo fallbacks to one by one
        fetching to find the culprit.
        """
        count_ok = 0
        count_error = 0
        self.stdout.write("Fetch all transporteurs for saving.")
        try:
            for transporteur in transporteurs_models.Transporteur.objects.iterator():
                transporteur.save()
                count_ok += 1
        except DatabaseError:
            self.stdout.write(
                self.style.WARNING(
                    "Fallback to check DB data, each model is fetched one by one by the ORM so be patient..."
                )
            )
            for transporteur_siret in transporteurs_models.Transporteur.objects.values_list('siret', flat=True):
                try:
                    transporteur = transporteurs_models.Transporteur.objects.get(pk=transporteur_siret)
                except transporteurs_models.Transporteur.DoesNotExist:
                    self.stderr.write(self.style.WARNING("Unable to get '%s'") % transporteur_siret)
                    self.stderr.write(self.style.ERROR("%s") % e)
                    count_error += 1
                    continue

                try:
                    transporteur.save()
                    count_ok += 1
                except DatabaseError as e:
                    self.stderr.write(self.style.WARNING("Unable to save '%s'") % transporteur)
                    self.stderr.write(self.style.ERROR("%s") % e)
                    count_error += 1

        self.stdout.write(self.style.SUCCESS("Transporteurs saved: %d" % count_ok))
        self.stdout.write(self.style.ERROR("Transporteurs to fix: %d" % count_error))
