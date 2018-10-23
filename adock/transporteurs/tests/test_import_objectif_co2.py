import datetime

from io import StringIO
from django.test import TestCase
from django.core.management import call_command

from .. import models
from .. import factories

from . import test


class ImportObjectifCO2TestCase(TestCase):
    def test_labelled(self):
        # Transporteur is present in the XLS file
        transporteur = factories.TransporteurFactory(
            siret=test.VALID_SIRET, departement=44
        )

        out = StringIO()
        call_command(
            "import_objectif_co2",
            "adock/transporteurs/tests/objectif-co2.xlsx",
            stdout=out,
        )

        out_value = out.getvalue()
        self.assertIn("Row 3: SIREN 123456404 of SIREN NOT FOUND not found.", out_value)
        self.assertIn(
            "Row 4: SIREN 123456789 and county 404 of COUNTY NOT FOUND not found.",
            out_value,
        )

        transporteur.refresh_from_db()
        self.assertEqual(transporteur.objectif_co2, models.OBJECTIF_CO2_LABELLED)
        self.assertEqual(transporteur.objectif_co2_begin, datetime.date(2018, 12, 7))
        self.assertEqual(transporteur.objectif_co2_end, datetime.date(2021, 12, 7))
