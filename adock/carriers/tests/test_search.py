from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from . import test
from .. import factories, models


class CarrierSearchTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.search_url = reverse("carriers_search")

    def get_carriers(self, params=None):
        """Helper"""
        response = self.client.get(self.search_url, params)
        self.assertEqual(response.status_code, 200)
        return response.json()["carriers"]


class CarrierSearchQueryTestCase(CarrierSearchTestCase):
    def test_one_invalid_param(self):
        response = self.client.get(self.search_url, {"wrong": test.VALID_SIRET})
        # Useless parameter is ignored
        self.assertEqual(response.status_code, 200)

    def test_empty_results_on_siren(self):
        carriers = self.get_carriers({"q": "123456789"})
        self.assertEqual(len(carriers), 0)

    def test_empty_results_on_siret(self):
        carriers = self.get_carriers({"q": test.VALID_SIRET})
        self.assertEqual(len(carriers), 0)

    def test_search_on_siret(self):
        factories.CarrierFactory(siret=test.VALID_SIRET)
        carriers = self.get_carriers({"q": test.VALID_SIRET})
        self.assertEqual(len(carriers), 1)
        self.assertEqual(carriers[0]["siret"], test.VALID_SIRET)

    def test_search_on_siret_and_code_postal(self):
        # Search on SIRET with spaces
        factories.CarrierFactory(siret=test.VALID_SIRET, code_postal="35000")
        carriers = self.get_carriers({"q": " " + test.VALID_SIRET[0:6]})
        self.assertEqual(len(carriers), 1)

        carriers = self.get_carriers({"q": "35 "})
        self.assertEqual(len(carriers), 1)

        carriers = self.get_carriers({"q": " " + test.VALID_SIRET[0:6] + ", 35"})
        self.assertEqual(len(carriers), 1)

        carriers = self.get_carriers({"q": " " + test.VALID_SIRET[0:6] + ", 37"})
        self.assertEqual(len(carriers), 0)

        carriers = self.get_carriers({"q": " 1" + test.VALID_SIRET[0:6] + ", 35"})
        self.assertEqual(len(carriers), 0)

    def test_search_on_enseigne(self):
        factories.CarrierFactory(enseigne="SUPER ROGER")
        carriers = self.get_carriers({"q": "rog"})
        self.assertEqual(len(carriers), 1)

        carriers = self.get_carriers({"q": "rg"})
        self.assertEqual(len(carriers), 0)

    def test_search_on_short_enseigne(self):
        factories.CarrierFactory(enseigne="123GO")
        carriers = self.get_carriers({"q": "3GO"})
        self.assertEqual(len(carriers), 1)

    def test_search_on_accentuated_enseigne(self):
        # Only uppercase strings in enseigne
        factories.CarrierFactory(enseigne="JEREMIE")
        factories.CarrierFactory(enseigne="JÉRÉMIE")
        factories.CarrierFactory(enseigne="BERNARD")

        carriers = self.get_carriers({"q": "jeremie"})
        self.assertEqual(len(carriers), 2, carriers)

        carriers = self.get_carriers({"q": "JERemie"})
        self.assertEqual(len(carriers), 2)

        carriers = self.get_carriers({"q": "JérÉmie"})
        self.assertEqual(len(carriers), 2)

    def test_search_on_code_postal(self):
        factories.CarrierFactory(enseigne="XPO BOIS DISTRIBUTION", code_postal="49000")
        carriers = self.get_carriers({"q": "xpo, DIS, 49"})
        self.assertEqual(len(carriers), 1)

        carriers = self.get_carriers({"q": "xpo DIS, 49"})
        self.assertEqual(len(carriers), 0)

    def test_search_ordering(self):
        # Name is set according to the expected ordering
        t3 = factories.CarrierFactory(enseigne="T3", email="")
        t4 = factories.CarrierFactory(enseigne="T4", email="", telephone="")
        t2 = factories.CarrierFactory(enseigne="T2")
        t1 = factories.CarrierFactory(enseigne="T1", validated_at=timezone.now())
        carriers = self.get_carriers({"q": "t"})
        self.assertEqual(len(carriers), 4)
        self.assertListEqual(
            [t["siret"] for t in carriers], [t.siret for t in [t1, t2, t3, t4]]
        )

    @override_settings(CARRIERS_LIMIT=2)
    def test_too_many_results(self):
        factories.CarrierFactory.create_batch(3, enseigne="FOO")
        response = self.client.get(self.search_url, {"q": "Foo"})
        data = response.json()
        self.assertEqual(data["limit"], 2)
        self.assertEqual(len(data["carriers"]), 2)

    def test_deleted(self):
        factories.CarrierFactory(raison_sociale="ACTIVE")
        factories.CarrierFactory(raison_sociale="DELETED", deleted_at=timezone.now())
        carriers = self.get_carriers()
        self.assertEqual(len(carriers), 1)
        self.assertEqual(carriers[0]["raison_sociale"], "ACTIVE")

    def test_sirene_deleted(self):
        factories.CarrierFactory(raison_sociale="ACTIVE")
        factories.CarrierFactory(
            raison_sociale="DELETED", sirene_deleted_at=timezone.now()
        )
        carriers = self.get_carriers()
        self.assertEqual(len(carriers), 1)
        self.assertEqual(carriers[0]["raison_sociale"], "ACTIVE")


class CarrierSearchLicenseTypeTestCase(CarrierSearchTestCase):
    def setUp(self):
        super().setUp()
        # No licenses is impossible in pratice
        factories.CarrierFactory(lti_numero="", lc_numero="")
        self.lti_only = factories.CarrierFactory(
            lti_numero="2018 84 0000393", lc_numero=""
        )
        self.lc_only = factories.CarrierFactory(
            lti_numero="", lc_numero="2017 84 0000285"
        )
        self.both = factories.CarrierFactory(
            lti_numero="2018 84 0000393", lc_numero="2018 84 0000392"
        )

    def test_no_license(self):
        carriers = self.get_carriers({"licence-types[]": ""})
        self.assertEqual(len(carriers), 4)

    def test_lti_only(self):
        carriers = self.get_carriers({"licence-types[]": ["lti"]})
        self.assertEqual(len(carriers), 2)
        self.assertSetEqual(
            {self.lti_only.siret, self.both.siret},
            {carrier["siret"] for carrier in carriers},
        )

    def test_lc_only(self):
        carriers = self.get_carriers({"licence-types[]": ["lc"]})
        self.assertEqual(len(carriers), 2)
        self.assertSetEqual(
            {self.lc_only.siret, self.both.siret},
            {carrier["siret"] for carrier in carriers},
        )

    def test_both(self):
        carriers = self.get_carriers({"licence-types[]": ["lti", "lc"]})
        self.assertEqual(len(carriers), 1)
        self.assertEqual(carriers[0]["siret"], self.both.siret)


class CarrierSearchDepartementTestCase(CarrierSearchTestCase):
    def setUp(self):
        super().setUp()
        factories.CarrierFactory(
            raison_sociale="UNDEFINED",
            working_area=models.WORKING_AREA_UNDEFINED,
            # Be sure filtering on working are is applied
            working_area_departements=["35", "44"],
        )
        factories.CarrierFactory(
            raison_sociale="INTERNATIONAL",
            working_area=models.WORKING_AREA_INTERNATIONAL,
        )
        factories.CarrierFactory(
            raison_sociale="FRANCE", working_area=models.WORKING_AREA_FRANCE
        )
        factories.CarrierFactory(
            raison_sociale="DEP. 35, 44",
            working_area=models.WORKING_AREA_DEPARTEMENT,
            working_area_departements=["35", "44"],
        )
        factories.CarrierFactory(
            raison_sociale="DEP. 72",
            working_area=models.WORKING_AREA_DEPARTEMENT,
            working_area_departements=["72"],
        )

    def test_search_invalid(self):
        response = response = self.client.get(
            self.search_url, {"departement-depart": "1000"}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(
            data["message"],
            "Le numéro de département français « 1000 » n'est pas valide.",
        )

    def test_search_international_france(self):
        carriers = self.get_carriers({"departement-depart": "93"})
        self.assertEqual(len(carriers), 2)
        # Ordering is consistent
        self.assertEqual(carriers[0]["raison_sociale"], "FRANCE")
        self.assertEqual(carriers[1]["raison_sociale"], "INTERNATIONAL")

    def test_search_one_departement(self):
        carriers = self.get_carriers({"q": "DEP. 35", "departement-depart": "35"})
        self.assertEqual(len(carriers), 1)

    def test_search_two_departements(self):
        carriers = self.get_carriers(
            {"q": "DEP. 35", "departement-depart": "35", "departement-arrivee": "44"}
        )
        self.assertEqual(len(carriers), 1)
        self.assertEqual(carriers[0]["raison_sociale"], "DEP. 35, 44")

    def test_search_two_departements_no_match(self):
        carriers = self.get_carriers(
            {"q": "DEP. 35", "departement-depart": "35", "departement-arrivee": "42"}
        )
        self.assertEqual(len(carriers), 0)

    def test_search_ordering(self):
        # Fewer number of departements first
        expected_ordering = (
            "DEP. 72",
            "DEP. 35, 44",
            "FRANCE",
            "INTERNATIONAL",
            "UNDEFINED",
        )
        carriers = self.get_carriers({})
        for i, raison_sociale in enumerate(expected_ordering):
            self.assertEqual(carriers[i]["raison_sociale"], raison_sociale)

    def test_search_ordering_with_departement_siege(self):
        factories.CarrierFactory(
            raison_sociale="DEP. 72 ET SIEGE 72",
            departement="72",
            working_area=models.WORKING_AREA_DEPARTEMENT,
            working_area_departements=["72"],
        )
        expected_ordering = (
            "DEP. 72 ET SIEGE 72",
            "DEP. 72",
            "FRANCE",
            "INTERNATIONAL",
        )
        carriers = self.get_carriers({"departement-arrivee": "72"})
        for i, raison_sociale in enumerate(expected_ordering):
            self.assertEqual(carriers[i]["raison_sociale"], raison_sociale)


class CarrierhSearchSpecialitiesTestCase(CarrierSearchTestCase):
    def setUp(self):
        super().setUp()
        factories.CarrierFactory(raison_sociale="NO SPECIALITIES", specialities=None)
        factories.CarrierFactory(raison_sociale="LOT", specialities=["LOT"])
        factories.CarrierFactory(
            raison_sociale="LOT, ANIMAL", specialities=["LOT", "ANIMAL"]
        )

    def test_no_filter(self):
        carriers = self.get_carriers({"specialities[]": []})
        self.assertEqual(len(carriers), 3)

    def test_one_speciality(self):
        """The carrier should provide one at least."""
        carriers = self.get_carriers({"specialities[]": ["LOT"]})
        self.assertEqual(len(carriers), 2)

        carriers = self.get_carriers({"specialities[]": ["ANIMAL"]})
        self.assertEqual(len(carriers), 1)

    def test_two_specialities(self):
        """The transport should provide the both."""
        carriers = self.get_carriers({"specialities[]": ["LOT", "ANIMAL"]})
        self.assertEqual(len(carriers), 1)
