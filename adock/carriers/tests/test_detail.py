import re

from django.core import mail
from django.conf import settings
from django.urls import reverse

from adock.accounts.test import AuthTestCaseBase

from . import test
from .. import factories, models, validators

PHONE = "+33240424546"
PHONE_DISPLAY = "02 40 42 45 46"
EMAIL = "foo@example.com"


class CarrierDetailTestCase(test.CarrierTestCaseMixin):
    def setUp(self):
        self.carrier = factories.CarrierFactory(
            siret=test.VALID_SIRET, with_editable=True
        )
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
        self.assertEqual(carrier_data["completeness"], 100.0)
        self.assertEqual(carrier_data["working_area"], "DEPARTEMENT")
        self.assertEqual(carrier_data["working_area_departements"], ["35", "44"])
        self.assertEqual(
            sorted(carrier_data["specialities"]), ["TEMPERATURE", "URBAIN"]
        )

        # To test JSON serialization with NULL values
        self.carrier.debut_activite = None
        self.carrier.save()

        # The delete will generate an automatic save to SET_NULL the editable
        self.carrier.editable.delete()

        # Empty editable
        self.carrier.editable = models.CarrierEditable.objects.create(
            carrier=self.carrier
        )
        self.carrier.save()

        response = self.client.get(self.detail_url)
        carrier_data = response.json()["carrier"]
        self.assertEqual(carrier_data["debut_activite"], None)
        self.assertEqual(carrier_data["specialities"], None)
        self.assertEqual(carrier_data["is_locked"], False)
        self.assertEqual(carrier_data["other_facilities"], [])
        self.assertEqual(carrier_data["latest_certificate"], None)

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

    def test_latest_certificate(self):
        certificate = factories.CarrierCertificateFactory(carrier=self.carrier)
        response = self.client.get(self.detail_url)
        carrier_data = response.json()["carrier"]
        self.assertEqual(
            carrier_data["latest_certificate"]["kind_display"],
            certificate.get_kind_display(),
        )

    def test_completeness(self):
        # The default factory sets all fields
        self.assertEqual(
            self.carrier.completeness,
            models.COMPLETENESS_PERCENT_MIN + 4 * models.EARNED_POINT_VALUE,
        )
        self.assertEqual(self.carrier.completeness, 100.0)

        # No telephone and no working area
        # Still email and specialities.
        self.carrier.editable.working_area = models.WORKING_AREA_UNDEFINED
        self.carrier.editable.telephone = ""
        self.assertEqual(
            self.carrier.compute_completeness(),
            models.COMPLETENESS_PERCENT_MIN + 2 * models.EARNED_POINT_VALUE,
        )

        # No email
        self.carrier.editable.email = ""
        self.assertEqual(
            self.carrier.compute_completeness(),
            models.COMPLETENESS_PERCENT_MIN + models.EARNED_POINT_VALUE,
        )

        # No specialities
        self.carrier.editable.specialities = None
        self.assertEqual(
            self.carrier.compute_completeness(), models.COMPLETENESS_PERCENT_MIN
        )

        # Compute is also triggered by save()
        self.carrier.save()
        self.assertEqual(self.carrier.completeness, models.COMPLETENESS_PERCENT_MIN)

    def test_post_unauthorized(self):
        self.post_carrier({"telephone": PHONE, "email": EMAIL}, 401)


class CarrierDetailPostTestCase(AuthTestCaseBase, test.CarrierTestCaseMixin):
    def setUp(self):
        super().setUp()
        self.carrier = factories.CarrierFactory(
            siret=test.VALID_SIRET, with_editable=True
        )
        self.detail_url = reverse(
            "carriers_detail", kwargs={"carrier_siret": self.carrier.siret}
        )
        self.http_authorization = self.log_in()

    def test_post_workflow(self):
        # Check initial status of factory
        self.assertNotEqual(self.carrier.editable.telephone, PHONE)
        self.assertNotEqual(self.carrier.editable.email, EMAIL)
        self.assertEqual(models.CarrierEditable.objects.count(), 1)

        # POST
        data = self.post_carrier_logged({"telephone": PHONE, "email": EMAIL}, 200)
        self.assertEqual(models.CarrierEditable.objects.count(), 2)

        # Not validated yet
        carrier = data["carrier"]
        self.assertEqual(carrier["telephone"], self.carrier.editable.telephone)
        self.assertEqual(carrier["email"], self.carrier.editable.email)

        # Check CarrierEditable to validate
        latest_editable = models.CarrierEditable.objects.latest()
        self.assertIsNone(latest_editable.confirmed_at)
        self.assertEqual(str(latest_editable.telephone), PHONE)
        self.assertEqual(latest_editable.email, EMAIL)

        # Mails:
        # 1. to notify previous user
        # 2. for confirmation of changes to new address
        # 3. to managers (changes)
        self.assertEqual(len(mail.outbox), 3)

        # 1
        self.assertEqual(
            mail.outbox[0].subject,
            "[A Dock] Notification de modification de votre fiche transporteur",
        )

        # 2
        self.assertEqual(
            mail.outbox[1].subject,
            "[A Dock] En attente de confirmation de votre fiche transporteur",
        )

        # 3
        message = "[A Dock] Modification du transporteur %s" % self.carrier.siret
        self.assertEqual(mail.outbox[2].subject, message)
        body = mail.outbox[2].body
        self.assertIn("telephone", body)
        self.assertIn("email", body)
        self.assertNotIn("working", body)

        # Confirm changes by extracting the token provided to the UI in #2 mail
        url_search = re.search(
            r"%stransporteur/changement/(?P<carrier_editable_id>\d+)/confirmer/(?P<token>.+)/"
            % settings.HTTP_CLIENT_URL,
            mail.outbox[1].body,
        )
        self.assertIsNotNone(url_search)

        results = url_search.groupdict()
        url_carrier_editable_confirm = reverse(
            "carriers_carrier_editable_confirm",
            kwargs={
                "carrier_editable_id": results["carrier_editable_id"],
                "token": results["token"],
            },
        )
        response = self.client.get(url_carrier_editable_confirm)
        self.assertEqual(response.status_code, 200)

        # Apply same changes so field comparison detects there is no changes
        mail.outbox = []

        data = self.post_carrier_logged({"telephone": PHONE, "email": EMAIL}, 200)
        self.assertEqual(models.CarrierEditable.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 0)

        self.carrier.refresh_from_db()
        self.assertEqual(self.carrier.editable, latest_editable)
        self.assertEqual(str(self.carrier.editable.telephone), PHONE)
        self.assertEqual(self.carrier.editable.email, EMAIL)
        self.assertIsNotNone(self.carrier.editable.created_at)
        self.assertEqual(self.carrier.editable.created_by, self.user)

    def test_post_response(self):
        NEW_PHONE = "+33240424546"
        NEW_EMAIL = "foo@example.com"

        # Apply changes with working area
        data = self.post_carrier_logged(
            {
                "telephone": NEW_PHONE,
                "email": NEW_EMAIL,
                "working_area": models.WORKING_AREA_DEPARTEMENT,
                "working_area_departements": ["45", "23", "976"],
                "specialities": ["LOT"],
            },
            200,
        )

        # HTTP Response (carrier unchanged)
        carrier = data["carrier"]
        self.assertEqual(carrier["telephone"], self.carrier.editable.telephone)
        self.assertEqual(carrier["email"], self.carrier.editable.email)
        self.assertEqual(carrier["working_area"], self.carrier.editable.working_area)
        self.assertEqual(
            carrier["working_area_departements"],
            self.carrier.editable.working_area_departements,
        )
        self.assertListEqual(
            carrier["specialities"], self.carrier.editable.specialities
        )
        self.assertEqual(carrier["completeness"], self.carrier.completeness)

        # Editable to confirm
        carrier_editable = models.CarrierEditable.objects.latest()
        self.assertEqual(carrier_editable.telephone, NEW_PHONE)
        self.assertEqual(carrier_editable.email, NEW_EMAIL)
        self.assertEqual(carrier_editable.working_area, models.WORKING_AREA_DEPARTEMENT)
        self.assertEqual(
            carrier_editable.working_area_departements, ["23", "45", "976"]
        )
        self.assertEqual(carrier_editable.specialities, ["LOT"])

    def test_post_website(self):
        WEBSITE = "http://www.example.com"
        self.assertNotEqual(self.carrier.editable.website, WEBSITE)
        data = self.post_carrier_logged(
            {"email": EMAIL, "telephone": PHONE, "website": WEBSITE}, 200
        )
        self.assertEqual(data["carrier"]["website"], self.carrier.editable.website)

        latest_editable = models.CarrierEditable.objects.latest()
        self.assertEqual(latest_editable.website, WEBSITE)

    def test_post_invalid_mimetype(self):
        response = self.client.post(
            self.detail_url, {"foo": "foo"}, HTTP_AUTHORIZATION=self.http_authorization
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["message"], "Le format des données n'est pas valide.")

    def test_post_invalid_payload(self):
        response = self.client.post(
            self.detail_url,
            "foo",
            "application/json",
            HTTP_AUTHORIZATION=self.http_authorization,
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["message"], "Le format des données n'est pas valide.")

    def test_post_unknown_payload(self):
        self.post_carrier_logged({"foo": "42"}, 400)

    def test_post_email_required(self):
        data = self.post_carrier_logged({"telephone": str(self.carrier.telephone)}, 400)
        self.assertEqual(data["errors"]["email"][0], "Ce champ est obligatoire.")

    def test_post_phone_required(self):
        data = self.post_carrier_logged({"email": self.carrier.email}, 400)
        self.assertEqual(data["errors"]["telephone"][0], "Ce champ est obligatoire.")

    def test_post_invalid_phone(self):
        data = self.post_carrier_logged(
            {"telephone": "11223344556", "email": self.carrier.email}, 400
        )
        self.assertEqual(
            data["errors"]["telephone"][0], "Le numéro saisi n'est pas valide."
        )

    def test_post_unexisting_working_area_departements(self):
        data = self.post_carrier_logged(
            {"telephone": PHONE, "email": EMAIL, "working_area_departements": ["20"]},
            400,
        )
        self.assertEqual(
            data["errors"]["working_area_departements"][0],
            "« 20 » n'est pas un département français valide.",
        )

    def test_post_invalid_working_area_departements(self):
        data = self.post_carrier_logged(
            {
                "telephone": PHONE,
                "email": EMAIL,
                "working_area_departements": ["2034;454"],
            },
            400,
        )
        self.assertEqual(
            data["errors"]["working_area_departements"]["0"][0],
            "Assurez-vous que ce champ comporte au plus 3 caractères.",
        )

    def test_post_empty_working_area_departements(self):
        data = self.post_carrier_logged(
            {
                "telephone": PHONE,
                "email": EMAIL,
                "working_area": models.WORKING_AREA_DEPARTEMENT,
                "working_area_departements": "",
            },
            400,
        )
        self.assertEqual(
            data["errors"]["working_area_departements"][0],
            # So bad translation and not helpful message...
            'Attendait une liste d\'éléments mais a reçu "str".',
        )

    def test_post_no_working_area_departements(self):
        data = self.post_carrier_logged(
            {
                "telephone": PHONE,
                "email": EMAIL,
                "working_area": models.WORKING_AREA_DEPARTEMENT,
                "working_area_departements": [],
            },
            400,
        )
        self.assertEqual(
            data["errors"]["working_area_departements"][0],
            "Des départements doivent être renseignés quand l'aire de travail est départementale.",
        )

    def test_post_format_working_area_departements(self):
        self.post_carrier_logged(
            {
                "telephone": PHONE,
                "email": EMAIL,
                "working_area": models.WORKING_AREA_DEPARTEMENT,
                "working_area_departements": ["2A", "5", "1", "10", "976"],
            },
            200,
        )
        carrier_editable = models.CarrierEditable.objects.latest()
        self.assertListEqual(
            carrier_editable.working_area_departements, ["01", "05", "10", "2A", "976"]
        )
