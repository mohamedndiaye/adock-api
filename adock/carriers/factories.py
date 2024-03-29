# pylint: disable=E1101
import datetime
import random
import string

import factory
from factory import fuzzy
import unidecode
from faker import Faker
from django.utils import timezone

from ..accounts import factories as accounts_factories
from . import models, validators

faker = Faker("fr_FR")


def get_lti_number(o, n):
    keys = ["82", "84", "93"]
    return "{} {} {:0>8}".format(o.lti_date_debut.year, random.choice(keys), n)


def compute_vat_number(siret):
    siren = siret[: validators.SIREN_LENGTH]
    try:
        key = (12 + 3 * (int(siren) % 97)) % 97
        return "FR%d%s" % (key, siren)
    except ValueError:
        return ""


class CarrierFactory(factory.django.DjangoModelFactory):
    siret = fuzzy.FuzzyText(length=validators.SIRET_LENGTH, chars=string.digits)
    numero_tva = factory.LazyAttribute(lambda o: compute_vat_number(o.siret))
    raison_sociale = factory.LazyAttribute(lambda _: faker.company().upper())
    enseigne = factory.LazyAttribute(lambda o: o.raison_sociale)
    enseigne_unaccent = factory.LazyAttribute(lambda o: unidecode.unidecode(o.enseigne))
    categorie_juridique = "Société par actions simplifiée (SAS)"
    adresse = factory.LazyAttribute(lambda _: faker.street_address().upper())
    code_postal = factory.Faker("zipcode")
    ville = factory.LazyAttribute(lambda _: faker.city().upper())
    telephone = factory.Faker("phone_number", locale="fr_FR")
    email = factory.Faker("email", locale="fr_FR")
    date_creation = fuzzy.FuzzyDate(datetime.date(1950, 1, 1))
    debut_activite = factory.LazyAttribute(lambda o: o.date_creation)
    code_ape = "4941A"
    libelle_ape = "Transports routiers de fret interurbains"
    gestionnaire = factory.LazyAttribute(lambda _: faker.name().upper())
    lti_numero = factory.LazyAttributeSequence(get_lti_number)
    lti_date_debut = fuzzy.FuzzyDate(datetime.date(2015, 1, 1))
    lti_date_fin = factory.LazyAttribute(
        lambda o: o.lti_date_debut + datetime.timedelta(days=6 * 364)
    )
    lti_nombre = fuzzy.FuzzyInteger(1, 20)
    editable = None

    @factory.post_generation
    def with_editable(self, create, extracted, **kwargs):
        """Allow to add editable with CarrierFactory(with_editable=True)"""
        if not create:
            return

        if extracted is True:
            self.editable = CarrierEditableFactory(carrier=self)
        elif extracted:
            self.editable = CarrierEditableFactory(carrier=self, **extracted)
            self.save()

    class Meta:
        model = models.Carrier


class CarrierCertificateFactory(factory.DjangoModelFactory):
    carrier = factory.SubFactory(CarrierFactory)
    kind = models.CERTIFICATE_NO_WORKERS
    confirmed_at = factory.LazyAttribute(lambda _: timezone.now())
    data = {
        "first_name": "Régis",
        "last_name": "Dujardin",
        "position": "Gérant",
        "location": "Saint André des Eaux",
    }

    class Meta:
        model = models.CarrierCertificate


class CarrierEditableFactory(factory.DjangoModelFactory):
    carrier = factory.SubFactory(CarrierFactory)
    telephone = factory.Faker("phone_number", locale="fr_FR")
    email = factory.Faker("email", locale="fr_FR")
    working_area = models.WORKING_AREA_DEPARTEMENT
    working_area_departements = ["35", "44"]
    specialities = ["TEMPERATURE", "URBAIN"]

    class Meta:
        model = models.CarrierEditable


class CarrierLicenseRenewalFactory(factory.DjangoModelFactory):
    carrier = factory.SubFactory(CarrierFactory)
    created_by = factory.SubFactory(accounts_factories.UserFactory)
    lti_nombre = fuzzy.FuzzyInteger(1, 20)
    lc_nombre = fuzzy.FuzzyInteger(1, 20)

    class Meta:
        model = models.CarrierLicenseRenewal


class CarrierUserFactory(factory.DjangoModelFactory):
    carrier = factory.SubFactory(CarrierFactory)
    user = factory.SubFactory(accounts_factories.UserFactory)

    class Meta:
        model = models.CarrierUser
