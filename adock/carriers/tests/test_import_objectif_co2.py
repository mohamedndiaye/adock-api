import datetime
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from . import test
from .. import factories, models


class ImportObjectifCO2TestCase(TestCase):
    def test_labelled(self):
        # Carrier is present in the XLS file
        carrier = factories.CarrierFactory(siret=test.VALID_SIRET, departement=44)

        out = StringIO()
        call_command(
            "import_objectif_co2", "adock/carriers/tests/objectif-co2.xlsx", stdout=out
        )

        out_value = out.getvalue()
        self.assertIn("Row 3: SIREN 123456404 of SIREN NOT FOUND not found.", out_value)
        self.assertIn(
            "Row 4: SIREN 123456789 and county 404 of COUNTY NOT FOUND not found.",
            out_value,
        )

        carrier.refresh_from_db()
        self.assertEqual(carrier.objectif_co2, models.OBJECTIF_CO2_LABELLED)
        self.assertEqual(carrier.objectif_co2_begin, datetime.date(2018, 12, 7))
        self.assertEqual(carrier.objectif_co2_end, datetime.date(2021, 12, 7))
