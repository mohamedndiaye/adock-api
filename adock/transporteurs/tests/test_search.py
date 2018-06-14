from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .. import factories
from .. import models
from . import test


class TransporteurSearchTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.search_url = reverse('transporteurs_recherche')

    def get_transporteurs(self, params=None):
        """Helper"""
        response = self.client.get(self.search_url, params)
        self.assertEqual(response.status_code, 200)
        return response.json()['results']


class TransporteurSearchQueryTestCase(TransporteurSearchTestCase):
    def test_one_invalid_param(self):
        response = self.client.get(self.search_url, {'wrong': test.VALID_SIRET})
        # Useless parameter is ignored
        self.assertEqual(response.status_code, 200)

    def test_empty_results_with_siren(self):
        transporteurs = self.get_transporteurs({'q': '123456789'})
        self.assertEqual(len(transporteurs), 0)

    def test_empty_results_with_siret(self):
        transporteurs = self.get_transporteurs({'q': test.VALID_SIRET})
        self.assertEqual(len(transporteurs), 0)

    def test_search_with_siret(self):
        factories.TransporteurFactory(siret=test.VALID_SIRET)
        transporteurs = self.get_transporteurs({'q': test.VALID_SIRET})
        self.assertEqual(len(transporteurs), 1)
        self.assertEqual(transporteurs[0]['siret'], test.VALID_SIRET)

    def test_search_with_siret_code_postal(self):
        # Search on SIRET with spaces
        factories.TransporteurFactory(
            siret=test.VALID_SIRET,
            code_postal='35000'
        )
        transporteurs = self.get_transporteurs({'q': ' ' + test.VALID_SIRET[0:6] + ', 35'})
        self.assertEqual(len(transporteurs), 1)

    def test_search_with_raison_sociale(self):
        factories.TransporteurFactory(raison_sociale='SUPER ROGER')
        transporteurs = self.get_transporteurs({'q': 'rog'})
        self.assertEqual(len(transporteurs), 1)

        transporteurs = self.get_transporteurs({'q': 'rg'})
        self.assertEqual(len(transporteurs), 0)

    def test_search_with_code_postal(self):
        factories.TransporteurFactory(
            raison_sociale='XPO BOIS DISTRIBUTION',
            code_postal='49000'
        )
        transporteurs = self.get_transporteurs({'q': 'xpo, DIS, 49'})
        self.assertEqual(len(transporteurs), 1)

        transporteurs = self.get_transporteurs({'q': 'xpo DIS, 49'})
        self.assertEqual(len(transporteurs), 0)

    def test_search_ordering(self):
        # Name is set according to the expected ordering
        t3 = factories.TransporteurFactory(raison_sociale='T3', email='')
        t4 = factories.TransporteurFactory(raison_sociale='T4', email='', telephone='')
        t2 = factories.TransporteurFactory(raison_sociale='T2')
        t1 = factories.TransporteurFactory(raison_sociale='T1', validated_at=timezone.now())
        transporteurs = self.get_transporteurs({'q': 't'})
        self.assertEqual(len(transporteurs), 4)
        self.assertListEqual(
            [t['siret'] for t in transporteurs],
            [t.siret for t in [t1, t2, t3, t4]])

    @override_settings(TRANSPORTEURS_LIMIT=2)
    def test_too_many_results(self):
        factories.TransporteurFactory.create_batch(3, raison_sociale='FOO')
        response = self.client.get(self.search_url, {'q': 'Foo'})
        data = response.json()
        self.assertEqual(data['limit'], 2)
        self.assertEqual(len(data['results']), 2)

    def test_deleted(self):
        factories.TransporteurFactory(raison_sociale='ACTIVE')
        factories.TransporteurFactory(raison_sociale='DELETED', deleted_at=timezone.now())
        transporteurs = self.get_transporteurs()
        self.assertEqual(len(transporteurs), 1)
        self.assertEqual(transporteurs[0]['raison_sociale'], 'ACTIVE')

class TransporteurSearchLicenseTypeTestCase(TransporteurSearchTestCase):

    def setUp(self):
        super().setUp()
        # No licenses is impossible in pratice
        factories.TransporteurFactory(lti_numero='', lc_numero='')
        self.lti_only = factories.TransporteurFactory(lti_numero='2018 84 0000393', lc_numero='')
        self.lc_only = factories.TransporteurFactory(lti_numero='', lc_numero='2017 84 0000285')
        self.both = factories.TransporteurFactory(lti_numero='2018 84 0000393', lc_numero='2018 84 0000392')

    def test_no_license(self):
        transporteurs = self.get_transporteurs({'licence-types[]': ''})
        self.assertEqual(len(transporteurs), 4)

    def test_lti_only(self):
        transporteurs = self.get_transporteurs({'licence-types[]': ['lti']})
        self.assertEqual(len(transporteurs), 2)
        self.assertSetEqual(
            set([self.lti_only.siret, self.both.siret]),
            set([transporteur['siret'] for transporteur in transporteurs]))

    def test_lc_only(self):
        transporteurs = self.get_transporteurs({'licence-types[]': ['lc']})
        self.assertEqual(len(transporteurs), 2)
        self.assertSetEqual(
            set([self.lc_only.siret, self.both.siret]),
            set([transporteur['siret'] for transporteur in transporteurs]))

    def test_both(self):
        transporteurs = self.get_transporteurs({'licence-types[]': ['lti', 'lc']})
        self.assertEqual(len(transporteurs), 1)
        self.assertEqual(transporteurs[0]['siret'], self.both.siret)


class TransporteurSearchDepartementTestCase(TransporteurSearchTestCase):

    def setUp(self):
        super().setUp()
        factories.TransporteurFactory(
            raison_sociale='UNDEFINED', working_area=models.WORKING_AREA_UNDEFINED,
            # Be sure filtering on working are is applied
            working_area_departements=['35', '44'])
        factories.TransporteurFactory(
            raison_sociale='INTERNATIONAL', working_area=models.WORKING_AREA_INTERNATIONAL)
        factories.TransporteurFactory(
            raison_sociale='FRANCE', working_area=models.WORKING_AREA_FRANCE)
        factories.TransporteurFactory(
            raison_sociale='DEP. 35, 44', working_area=models.WORKING_AREA_DEPARTEMENT,
            working_area_departements=['35', '44'])
        factories.TransporteurFactory(
            raison_sociale='DEP. 72', working_area=models.WORKING_AREA_DEPARTEMENT,
            working_area_departements=['72'])

    def test_search_invalid(self):
        response = response = self.client.get(
            self.search_url,
            {'departement-depart': '1000'}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['message'], "Le numéro de département français « 1000 » n'est pas valide.")

    def test_search_international_france(self):
        transporteurs = self.get_transporteurs({'departement-depart': '93'})
        self.assertEqual(len(transporteurs), 2)
        # Ordering is consistent
        self.assertEqual(transporteurs[0]['raison_sociale'], 'FRANCE')
        self.assertEqual(transporteurs[1]['raison_sociale'], 'INTERNATIONAL')

    def test_search_one_departement(self):
        transporteurs = self.get_transporteurs({
            'q': 'DEP. 35',
            'departement-depart': '35'
        })
        self.assertEqual(len(transporteurs), 1)

    def test_search_two_departements(self):
        transporteurs = self.get_transporteurs({
            'q': 'DEP. 35',
            'departement-depart': '35',
            'departement-arrivee': '44'
        })
        self.assertEqual(len(transporteurs), 1)
        self.assertEqual(transporteurs[0]['raison_sociale'], 'DEP. 35, 44')

    def test_search_two_departements_no_match(self):
        transporteurs = self.get_transporteurs({
            'q': 'DEP. 35',
            'departement-depart': '35',
            'departement-arrivee': '42'
        })
        self.assertEqual(len(transporteurs), 0)

    def test_search_ordering(self):
        # Fewer number of departements first
        expected_ordering = (
            'DEP. 72',
            'DEP. 35, 44',
            'FRANCE',
            'INTERNATIONAL',
            'UNDEFINED'
        )
        transporteurs = self.get_transporteurs({})
        for i, raison_sociale in enumerate(expected_ordering):
            self.assertEqual(transporteurs[i]['raison_sociale'], raison_sociale)

    def test_search_ordering_with_departement_siege(self):
        factories.TransporteurFactory(
            raison_sociale='DEP. 72 ET SIEGE 72',
            departement='72',
            working_area=models.WORKING_AREA_DEPARTEMENT,
            working_area_departements=['72'])
        expected_ordering = (
            'DEP. 72 ET SIEGE 72',
            'DEP. 72',
            'FRANCE',
            'INTERNATIONAL',
        )
        transporteurs = self.get_transporteurs({'departement-arrivee': '72'})
        for i, raison_sociale in enumerate(expected_ordering):
            self.assertEqual(transporteurs[i]['raison_sociale'], raison_sociale)

class TransporteurSearchSpecialitiesTestCase(TransporteurSearchTestCase):

    def setUp(self):
        super().setUp()
        factories.TransporteurFactory(raison_sociale='NO SPECIALITIES', specialities=None)
        factories.TransporteurFactory(raison_sociale='LOT', specialities=['LOT'])
        factories.TransporteurFactory(raison_sociale='LOT, ANIMAL', specialities=['LOT', 'ANIMAL'])

    def test_no_filter(self):
        transporteurs = self.get_transporteurs({'specialities[]': []})
        self.assertEqual(len(transporteurs), 3)

    def test_one_speciality(self):
        """The transporteur should provide one at least."""
        transporteurs = self.get_transporteurs({'specialities[]': ['LOT']})
        self.assertEqual(len(transporteurs), 2)

        transporteurs = self.get_transporteurs({'specialities[]': ['ANIMAL']})
        self.assertEqual(len(transporteurs), 1)

    def test_two_specialities(self):
        """The transport should provide the both."""
        transporteurs = self.get_transporteurs({'specialities[]': ['LOT', 'ANIMAL']})
        self.assertEqual(len(transporteurs), 1)
