from django.core import mail
from django.urls import reverse
from django.utils import timezone

from . import test
from .. import factories, models, validators

PHONE = "+33240424546"
PHONE_DISPLAY = "02 40 42 45 46"
EMAIL = "foo@example.com"


class CarrierDetailTestCase(test.CarrierTestCase):
    def setUp(self):
        self.carrier = factories.CarrierFactory(siret=test.VALID_SIRET)
        self.detail_url = reverse(
            "carriers_detail", kwargs={"carrier_siret": self.carrier.siret}
        )

    def test_get(self):
        response = self.client.get(self.detail_url)
        carrier_data = response.json()["carrier"]
        self.assertEqual(carrier_data["siret"], test.VALID_SIRET)
        self.assertEqual(carrier_data["raison_sociale"], self.carrier.raison_sociale)
        self.assertEqual(
            carrier_data["debut_activite"], str(self.carrier.debut_activite)
        )
        # Two original fields not validated, working area and specialities => 3 points
        self.assertEqual(
            carrier_data["completeness"],
            models.COMPLETENESS_PERCENT_MIN + 3 * models.EARNED_POINT_VALUE,
        )
        self.assertEqual(carrier_data["working_area"], "DEPARTEMENT")
        self.assertEqual(carrier_data["working_area_departements"], ["35", "44"])
        self.assertEqual(
            sorted(carrier_data["specialities"]), ["TEMPERATURE", "URBAIN"]
        )

        # To test JSON serialization with NULL values
        self.carrier.debut_activite = None
        self.carrier.specialities = None
        self.carrier.save()
        response = self.client.get(self.detail_url)
        carrier_data = response.json()["carrier"]
        self.assertEqual(carrier_data["debut_activite"], None)
        self.assertEqual(carrier_data["specialities"], None)
        self.assertEqual(carrier_data["is_locked"], False)
        self.assertEqual(carrier_data["other_facilities"], [])

    def test_get_other_facilities(self):
        for i in range(3):
            siret = "{siren}{i:05}".format(
                siren=self.carrier.siret[  # pylint: disable=E1136
                    : validators.SIREN_LENGTH
                ],
                i=i,
            )
            factories.CarrierFactory(siret=siret)

        response = self.client.get(self.detail_url)
        carrier_data = response.json()["carrier"]
        self.assertEqual(len(carrier_data["other_facilities"]), 3)
        self.assertIn("siret", carrier_data["other_facilities"][0])

    def test_get_empty_phone(self):
        self.carrier.telephone = ""
        self.carrier.save()
        response = self.client.get(self.detail_url)
        data = response.json()
        self.assertEqual(data["carrier"]["telephone"], "")

    def test_get_no_email(self):
        response = self.client.get(self.detail_url)
        data = response.json()
        self.assertNotIn("email", data["carrier"])

    def get_get_mail(self):
        self.carrier.validated_at = timezone.now
        self.carrier.save()
        response = self.client.get(self.detail_url)
        data = response.json()
        self.assertIn("email", data["carrier"])

    def test_patch_log(self):
        old_phone = self.carrier.telephone
        carrier = self.patch_carrier({"telephone": PHONE}, 200)["carrier"]
        # Initial and new entry
        self.assertEqual(models.CarrierLog.objects.count(), 2)
        carrier_log = models.CarrierLog.objects.earliest("pk")
        # Only one field changed
        self.assertEqual(len(carrier_log.data), 1)
        # Old value
        self.assertEqual(carrier_log.data["telephone"], str(old_phone))
        # New value
        carrier_log = models.CarrierLog.objects.latest("pk")
        self.assertEqual(carrier_log.data["telephone"], PHONE)
        self.assertEqual(carrier["telephone"], PHONE_DISPLAY)

        self.carrier.refresh_from_db()
        self.patch_carrier(
            {"telephone": PHONE, "working_area_departements": "2A, 56"}, 200
        )
        # Only one new entry
        self.assertEqual(models.CarrierLog.objects.count(), 3)
        # Only working area has changed
        carrier_log = models.CarrierLog.objects.latest("pk")
        self.assertEqual(len(carrier_log.data), 1)
        # New value
        self.assertEqual(carrier_log.data["working_area_departements"], ["2A", "56"])

        self.patch_carrier(
            {
                "telephone": PHONE,
                "email": EMAIL,
                "working_area_departements": "2A, 57",
                # Should be ignored from log
                "edit_code": "123456",
            },
            200,
        )
        self.assertEqual(models.CarrierLog.objects.count(), 4)
        # Only working area and email have changed
        carrier_log = models.CarrierLog.objects.latest("pk")
        self.assertEqual(len(carrier_log.data), 2)
        self.assertIn("email", carrier_log.data)
        self.assertIn("working_area_departements", carrier_log.data)

    def test_patch_phone_email(self):
        # Initial status
        self.assertNotEqual(self.carrier.telephone, PHONE)
        self.assertNotEqual(self.carrier.email, EMAIL)

        # Apply changes w/o working area
        data = self.patch_carrier({"telephone": PHONE, "email": EMAIL}, 200)

        carrier = data["carrier"]
        self.assertEqual(carrier["telephone"], PHONE_DISPLAY)
        self.assertEqual(carrier["email"], EMAIL)
        self.assertTrue(data["confirmation_email_sent"])

        # One mail for the user and another for the managers
        self.assertEqual(len(mail.outbox), 2)

        # Mail manager about applied changes
        message = "[adock] Modification du transporteur %s" % self.carrier.siret
        self.assertEqual(mail.outbox[0].subject, message)
        self.assertIn("telephone", mail.outbox[0].body)
        self.assertIn("email", mail.outbox[0].body)
        self.assertNotIn("working", mail.outbox[0].body)

        # Mail user to confirm email
        self.assertEqual(
            mail.outbox[1].subject,
            "A Dock - Confirmation de votre adresse électronique",
        )

        # Apply same changes so field comparison detects there is no changes
        data = self.patch_carrier({"telephone": PHONE, "email": EMAIL}, 200)
        self.assertFalse(data["confirmation_email_sent"])

    def test_patch_partial_completeness(self):
        # Remove other fields
        self.carrier.working_area = models.WORKING_AREA_UNDEFINED
        self.carrier.specialities = None
        self.carrier.save()
        data = self.patch_carrier({"telephone": PHONE, "email": EMAIL}, 200)
        self.carrier.refresh_from_db()
        self.assertEqual(data["carrier"]["completeness"], self.carrier.completeness)
        self.assertEqual(
            self.carrier.completeness,
            models.COMPLETENESS_PERCENT_MIN + 2 * models.EARNED_POINT_VALUE,
        )

    def test_patch_full_completeness(self):
        NEW_PHONE = "+33240424546"
        NEW_EMAIL = "foo@example.com"

        # Apply changes with working area
        data = self.patch_carrier(
            {
                "telephone": NEW_PHONE,
                "email": NEW_EMAIL,
                "working_area": models.WORKING_AREA_DEPARTEMENT,
                "working_area_departements": ["45", "23", "976"],
                "specialities": ["LOT"],
            },
            200,
        )

        # Side effects
        carrier = data["carrier"]
        self.assertEqual(carrier["telephone"], "02 40 42 45 46")
        self.assertEqual(carrier["email"], NEW_EMAIL)
        self.assertEqual(carrier["working_area"], models.WORKING_AREA_DEPARTEMENT)
        self.assertEqual(carrier["working_area_departements"], ["23", "45", "976"])
        self.assertListEqual(carrier["specialities"], ["LOT"])
        self.assertEqual(carrier["completeness"], 100)
        self.assertEqual(len(mail.outbox), 2)

        # Be sure the response is identical to the DB
        self.carrier.refresh_from_db()
        self.assertEqual(self.carrier.telephone, NEW_PHONE)
        self.assertEqual(self.carrier.email, NEW_EMAIL)
        self.assertEqual(self.carrier.working_area, models.WORKING_AREA_DEPARTEMENT)
        self.assertEqual(self.carrier.working_area_departements, ["23", "45", "976"])
        self.assertEqual(self.carrier.specialities, ["LOT"])
        self.assertEqual(self.carrier.completeness, 100)

    def test_patch_website(self):
        WEBSITE = "http://www.example.com"
        data = self.patch_carrier({"website": "www.example.com"}, 200)
        self.assertEqual(data["carrier"]["website"], WEBSITE)
        # Mail sent on first validation
        self.assertTrue(data["confirmation_email_sent"])
        self.carrier.refresh_from_db()
        self.assertEqual(self.carrier.website, WEBSITE)

        self.assertEqual(len(mail.outbox), 2)
        message = "[adock] Modification du transporteur %s" % self.carrier.siret
        self.assertEqual(mail.outbox[0].subject, message)

    def test_patch_invalid_request(self):
        response = self.client.patch(self.detail_url, {"foo": "foo"})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(
            data["message"], "Seules les requêtes PATCH en JSON sont prises en charge."
        )

    def test_patch_invalid_payload(self):
        response = self.client.patch(self.detail_url, "foo", "application/json")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["message"], "Les données ne sont pas valides.")

    def test_patch_unknow_payload(self):
        data = self.patch_carrier({"foo": "42"}, 200)
        self.assertNotIn("foo", data["carrier"])

    def test_patch_phone_required(self):
        # Accepted
        data = self.patch_carrier({"email": self.carrier.email}, 200)

        # Remove phone on the instance
        self.carrier.telephone = ""
        self.carrier.save()

        # Only possible to PATCH w/o phone when the carrier already contains a phone
        data = self.patch_carrier({"email": self.carrier.email}, 400)
        self.assertEqual(data["telephone"][0], "Ce champ est obligatoire.")

        data = self.patch_carrier(
            {"telephone": PHONE, "email": self.carrier.email}, 200
        )

    def test_patch_invalid_phone(self):
        data = self.patch_carrier(
            {"telephone": "11223344556", "email": self.carrier.email}, 400
        )

        # Wrong French translation will be fixed in django-phonenumber-field > 2.0.1 (my patch)
        # https://github.com/stefanfoulis/django-phonenumber-field/issues/233
        self.assertEqual(data["telephone"][0], "Entrez un numéro de téléphone valide.")

    def test_patch_unexisting_working_area_departements(self):
        data = self.patch_carrier({"working_area_departements": ["20"]}, 400)
        self.assertEqual(
            data["working_area_departements"][0],
            "« 20 » n'est pas un département français valide.",
        )

    def test_patch_invalid_working_area_departements(self):
        data = self.patch_carrier({"working_area_departements": ["2034;454"]}, 400)
        self.assertEqual(
            data["working_area_departements"][0],
            "L'élément n°1 du tableau n'est pas valide : "
            "Assurez-vous que cette valeur comporte au plus 3 caractères (actuellement 8).",
        )

    def test_patch_no_working_area_departements(self):
        data = self.patch_carrier(
            {
                "working_area": models.WORKING_AREA_DEPARTEMENT,
                "working_area_departements": "",
            },
            400,
        )
        self.assertEqual(
            data["working_area_departements"][0],
            "Des départements doivent être renseignés quand l'aire de travail est départementale.",
        )

    def test_patch_format_working_area_departements(self):
        self.patch_carrier(
            {
                "working_area": models.WORKING_AREA_DEPARTEMENT,
                "working_area_departements": "2A, 5, 1, 10, 976",
            },
            200,
        )
        self.carrier.refresh_from_db()
        self.assertListEqual(
            self.carrier.working_area_departements, ["01", "05", "10", "2A", "976"]
        )

    def test_completeness(self):
        # The default factory sets telephone and email but they aren't validated
        # a working area and specialities.
        self.assertEqual(
            self.carrier.completeness,
            models.COMPLETENESS_PERCENT_MIN + 3 * models.EARNED_POINT_VALUE,
        )

        # No telephone and no working area
        # Still email not validated and specialities.
        self.carrier.working_area = models.WORKING_AREA_UNDEFINED
        self.carrier.telephone = ""
        self.carrier.save()
        self.assertEqual(
            self.carrier.completeness,
            models.COMPLETENESS_PERCENT_MIN + 1.5 * models.EARNED_POINT_VALUE,
        )

        # No email
        self.carrier.email = ""
        self.carrier.save()
        self.assertEqual(
            self.carrier.completeness,
            models.COMPLETENESS_PERCENT_MIN + models.EARNED_POINT_VALUE,
        )

        # No specialities
        self.carrier.specialities = None
        self.carrier.save()
        self.assertEqual(self.carrier.completeness, models.COMPLETENESS_PERCENT_MIN)

        # Updated email
        self.carrier.email = "foo@example.com"
        self.carrier.validated_at = timezone.now()
        self.carrier.save()
        self.assertEqual(
            self.carrier.completeness,
            models.COMPLETENESS_PERCENT_MIN + models.EARNED_POINT_VALUE,
        )

        # Phone and email validated
        self.carrier.telephone = "02 40 41 42 43"
        self.carrier.validated_at = timezone.now()
        self.carrier.save()
        self.assertEqual(
            self.carrier.completeness,
            models.COMPLETENESS_PERCENT_MIN + 2 * models.EARNED_POINT_VALUE,
        )

        # Add working area and specialities
        # Completeful 100%
        self.carrier.working_area = models.WORKING_AREA_DEPARTEMENT
        self.carrier.specialities = ["LOT"]
        self.carrier.save()
        self.assertEqual(self.carrier.completeness, 100)
