from django.core import mail
from django.urls import reverse
from django.utils import timezone

from . import test
from .. import factories
from .. import models
from .. import validators

PHONE = '+33240424546'
PHONE_DISPLAY = '02 40 42 45 46'
EMAIL = 'foo@example.com'


class TransporteurDetailTestCase(test.TransporteurTestCase):
    def setUp(self):
        self.transporteur = factories.TransporteurFactory(siret=test.VALID_SIRET)
        self.detail_url = reverse(
            'transporteurs_detail',
            kwargs={'transporteur_siret': self.transporteur.siret}
        )

    def test_get(self):
        response = self.client.get(self.detail_url)
        transporteur_data = response.json()['transporteur']
        self.assertEqual(transporteur_data['siret'], test.VALID_SIRET)
        self.assertEqual(transporteur_data['raison_sociale'], self.transporteur.raison_sociale)
        self.assertEqual(transporteur_data['debut_activite'], str(self.transporteur.debut_activite))
        # Two original fields not validated, working area and specialities => 3 points
        self.assertEqual(
            transporteur_data['completeness'],
            models.COMPLETENESS_PERCENT_MIN + 3 * models.EARNED_POINT_VALUE)
        self.assertEqual(transporteur_data['working_area'], 'DEPARTEMENT')
        self.assertEqual(transporteur_data['working_area_departements'], ['35', '44'])
        self.assertEqual(
            sorted(transporteur_data['specialities']),
            ['TEMPERATURE', 'URBAIN']
        )

        # To test JSON serialization with NULL values
        self.transporteur.debut_activite = None
        self.transporteur.specialities = None
        self.transporteur.save()
        response = self.client.get(self.detail_url)
        transporteur_data = response.json()['transporteur']
        self.assertEqual(transporteur_data['debut_activite'], None)
        self.assertEqual(transporteur_data['specialities'], None)
        self.assertEqual(transporteur_data['is_locked'], False)
        self.assertEqual(transporteur_data['subsidiaries'], [])

    def test_get_subsidiaries(self):
        for i in range(3):
            siret = "{siren}{i:05}".format(
                siren=self.transporteur.siret[:validators.SIREN_LENGTH], # pylint: disable=E1136
                i=i
            )
            factories.TransporteurFactory(siret=siret)

        response = self.client.get(self.detail_url)
        transporteur_data = response.json()['transporteur']
        self.assertEqual(len(transporteur_data['subsidiaries']), 3)
        self.assertIn('siret', transporteur_data['subsidiaries'][0])

    def test_get_empty_phone(self):
        self.transporteur.telephone = ''
        self.transporteur.save()
        response = self.client.get(self.detail_url)
        data = response.json()
        self.assertEqual(data['transporteur']['telephone'], '')

    def test_patch_log(self):
        transporteur = self.patch_transporteur(
            {
                'telephone': PHONE,
            },
            200
        )['transporteur']
        self.assertEqual(models.TransporteurLog.objects.count(), 1)
        transporteur_log = models.TransporteurLog.objects.get()
        # Only one field changed
        self.assertEqual(len(transporteur_log.data), 1)
        # Old value
        self.assertEqual(transporteur_log.data['telephone'], str(self.transporteur.telephone))
        # New value
        self.assertEqual(transporteur['telephone'], PHONE_DISPLAY)

        self.transporteur.refresh_from_db()
        self.patch_transporteur(
            {
                'telephone': PHONE,
                'working_area_departements': '2A, 56',
            },
            200
        )
        self.assertEqual(models.TransporteurLog.objects.count(), 2)
        # Only working area has changed
        transporteur_log = models.TransporteurLog.objects.order_by('-pk').first()
        self.assertEqual(len(transporteur_log.data), 1)
        # Old value
        self.assertEqual(
            transporteur_log.data['working_area_departements'],
            str(self.transporteur.working_area_departements)
        )

        self.transporteur.refresh_from_db()
        self.patch_transporteur(
            {
                'telephone': PHONE,
                'email': EMAIL,
                'working_area_departements': '2A, 57',
                # Should be ignored from log
                'edit_code': '123456'
            },
            200
        )
        self.assertEqual(models.TransporteurLog.objects.count(), 3)
        # Only working area and email have changed
        transporteur_log = models.TransporteurLog.objects.order_by('-pk').first()
        self.assertEqual(len(transporteur_log.data), 2)
        self.assertIn('email', transporteur_log.data)
        self.assertIn('working_area_departements', transporteur_log.data)

    def test_patch_phone_email(self):
        # Initial status
        self.assertNotEqual(self.transporteur.telephone, PHONE)
        self.assertNotEqual(self.transporteur.email, EMAIL)

        # Apply changes w/o working area
        data = self.patch_transporteur(
            {
                'telephone': PHONE,
                'email': EMAIL
            },
            200
        )

        transporteur = data['transporteur']
        self.assertEqual(transporteur['telephone'], PHONE_DISPLAY)
        self.assertEqual(transporteur['email'], EMAIL)
        self.assertTrue(data['confirmation_email_sent'])

        # One mail for the user and another for the managers
        self.assertEqual(len(mail.outbox), 2)

        # Mail manager about applied changes
        message = "[adock] Modification du transporteur %s" % self.transporteur.siret
        self.assertEqual(mail.outbox[0].subject, message)
        self.assertIn('telephone', mail.outbox[0].body)
        self.assertIn('email', mail.outbox[0].body)
        self.assertNotIn('working', mail.outbox[0].body)

        # Mail user to confirm email
        self.assertEqual(
            mail.outbox[1].subject,
            "A Dock - Confirmation de votre adresse électronique"
        )

        # Apply same changes so field comparison detects there is no changes
        data = self.patch_transporteur(
            {
                'telephone': PHONE,
                'email': EMAIL
            },
            200
        )
        self.assertFalse(data['confirmation_email_sent'])

    def test_patch_partial_completeness(self):
        # Remove other fields
        self.transporteur.working_area = models.WORKING_AREA_UNDEFINED
        self.transporteur.specialities = None
        self.transporteur.save()
        data = self.patch_transporteur(
            {
                'telephone': PHONE,
                'email': EMAIL
            },
            200
        )
        self.transporteur.refresh_from_db()
        self.assertEqual(data['transporteur']['completeness'], self.transporteur.completeness)
        self.assertEqual(
            self.transporteur.completeness,
            models.COMPLETENESS_PERCENT_MIN + 2 * models.EARNED_POINT_VALUE
        )

    def test_patch_full_completeness(self):
        NEW_PHONE = '+33240424546'
        NEW_EMAIL = 'foo@example.com'

        # Apply changes with working area
        data = self.patch_transporteur(
            {
                'telephone': NEW_PHONE,
                'email': NEW_EMAIL,
                'working_area': models.WORKING_AREA_DEPARTEMENT,
                'working_area_departements': ['45', '23', '976'],
                'specialities': ['LOT'],
            },
            200
        )

        # Side effects
        transporteur = data['transporteur']
        self.assertEqual(transporteur['telephone'], '02 40 42 45 46')
        self.assertEqual(transporteur['email'], NEW_EMAIL)
        self.assertEqual(transporteur['working_area'], models.WORKING_AREA_DEPARTEMENT)
        self.assertEqual(transporteur['working_area_departements'], ['23', '45', '976'])
        self.assertListEqual(transporteur['specialities'], ['LOT'])
        self.assertEqual(transporteur['completeness'], 100)
        self.assertEqual(len(mail.outbox), 2)

        # Be sure the response is identical to the DB
        self.transporteur.refresh_from_db()
        self.assertEqual(self.transporteur.telephone, NEW_PHONE)
        self.assertEqual(self.transporteur.email, NEW_EMAIL)
        self.assertEqual(self.transporteur.working_area, models.WORKING_AREA_DEPARTEMENT)
        self.assertEqual(self.transporteur.working_area_departements, ['23', '45', '976'])
        self.assertEqual(self.transporteur.specialities, ['LOT'])
        self.assertEqual(self.transporteur.completeness, 100)

    def test_patch_website(self):
        WEBSITE = 'http://www.example.com'
        data = self.patch_transporteur(
            {
                'website': 'www.example.com',
            },
            200
        )
        self.assertEqual(data['transporteur']['website'], WEBSITE)
        # Mail sent on first validation
        self.assertTrue(data['confirmation_email_sent'])
        self.transporteur.refresh_from_db()
        self.assertEqual(self.transporteur.website, WEBSITE)

        self.assertEqual(len(mail.outbox), 2)
        message = "[adock] Modification du transporteur %s" % self.transporteur.siret
        self.assertEqual(mail.outbox[0].subject, message)

    def test_patch_invalid_request(self):
        response = self.client.patch(self.detail_url, {'foo': 'foo'})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['message'], 'Seules les requêtes PATCH en JSON sont prises en charge.')

    def test_patch_invalid_payload(self):
        response = self.client.patch(self.detail_url, 'foo', 'application/json')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['message'], 'Les données ne sont pas valides.')

    def test_patch_unknow_payload(self):
        data = self.patch_transporteur(
            {
                'foo': '42',
            },
            200
        )
        self.assertNotIn('foo', data['transporteur'])

    def test_patch_phone_required(self):
        # Accepted
        data = self.patch_transporteur(
            {
                'email': self.transporteur.email,
            },
            200
        )

        # Remove phone on the instance
        self.transporteur.telephone = ''
        self.transporteur.save()

        # Only possible to PATCH w/o phone when the transporteur already contains a phone
        data = self.patch_transporteur(
            {
                'email': self.transporteur.email,
            },
            400
        )
        self.assertEqual(data['telephone'][0], "Ce champ est obligatoire.")

        data = self.patch_transporteur(
            {
                'telephone': PHONE,
                'email': self.transporteur.email,
            },
            200
        )

    def test_patch_invalid_phone(self):
        data = self.patch_transporteur(
            {
                'telephone': '11223344556',
                'email': self.transporteur.email,
            },
            400
        )
        # Wrong French translation will be fixed in django-phonenumber-field > 2.0 (my patch)
        self.assertEqual(data['telephone'][0], "Entrez un numéro de téléphone valide.")

    def test_patch_unexisting_working_area_departements(self):
        data = self.patch_transporteur(
            {
                'working_area_departements': ['20'],
            },
            400
        )
        self.assertEqual(
            data['working_area_departements'][0],
            "« 20 » n'est pas un département français valide."
        )

    def test_patch_invalid_working_area_departements(self):
        data = self.patch_transporteur(
            {
                'working_area_departements': ['2034;454'],
            },
            400
        )
        self.assertEqual(
            data['working_area_departements'][0],
            "L'élément n°1 du tableau n'est pas valide : "
            "Assurez-vous que cette valeur comporte au plus 3 caractères (actuellement 8)."
        )

    def test_patch_no_working_area_departements(self):
        data = self.patch_transporteur(
            {
                'working_area': models.WORKING_AREA_DEPARTEMENT,
                'working_area_departements': '',
            },
            400
        )
        self.assertEqual(
            data['working_area_departements'][0],
            "Des départements doivent être renseignés quand l'aire de travail est départementale."
        )

    def test_patch_format_working_area_departements(self):
        self.patch_transporteur(
            {
                'working_area': models.WORKING_AREA_DEPARTEMENT,
                'working_area_departements': '2A, 5, 1, 10, 976',
            },
            200
        )
        self.transporteur.refresh_from_db()
        self.assertListEqual(
            self.transporteur.working_area_departements,
            ['01', '05', '10', '2A', '976']
        )

    def test_completeness(self):
        # The default factory sets telephone and email but they aren't validated
        # a working area and specialities.
        self.assertEqual(
            self.transporteur.completeness,
            models.COMPLETENESS_PERCENT_MIN + 3 * models.EARNED_POINT_VALUE
        )

        # No telephone and no working area
        # Still email not validated and specialities.
        self.transporteur.working_area = models.WORKING_AREA_UNDEFINED
        self.transporteur.telephone = ''
        self.transporteur.save()
        self.assertEqual(
            self.transporteur.completeness,
            models.COMPLETENESS_PERCENT_MIN + 1.5 * models.EARNED_POINT_VALUE
        )

        # No email
        self.transporteur.email = ''
        self.transporteur.save()
        self.assertEqual(
            self.transporteur.completeness,
            models.COMPLETENESS_PERCENT_MIN + models.EARNED_POINT_VALUE
        )

        # No specialities
        self.transporteur.specialities = None
        self.transporteur.save()
        self.assertEqual(
            self.transporteur.completeness,
            models.COMPLETENESS_PERCENT_MIN
        )

        # Updated email
        self.transporteur.email = 'foo@example.com'
        self.transporteur.validated_at = timezone.now()
        self.transporteur.save()
        self.assertEqual(
            self.transporteur.completeness,
            models.COMPLETENESS_PERCENT_MIN + models.EARNED_POINT_VALUE
        )

        # Phone and email validated
        self.transporteur.telephone = '02 40 41 42 43'
        self.transporteur.validated_at = timezone.now()
        self.transporteur.save()
        self.assertEqual(
            self.transporteur.completeness,
            models.COMPLETENESS_PERCENT_MIN + 2 * models.EARNED_POINT_VALUE
        )

        # Add working area and specialities
        # Completeful 100%
        self.transporteur.working_area = models.WORKING_AREA_DEPARTEMENT
        self.transporteur.specialities = ['LOT']
        self.transporteur.save()
        self.assertEqual(self.transporteur.completeness, 100)
