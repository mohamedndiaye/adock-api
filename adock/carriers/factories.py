# pylint: disable=E1101
import datetime
import random
import string

import factory
from factory import fuzzy
import unidecode
from faker import Faker

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
    working_area = models.WORKING_AREA_DEPARTEMENT
    working_area_departements = ["35", "44"]
    specialities = ["TEMPERATURE", "URBAIN"]

    class Meta:
        model = models.Carrier


class CarrierCertificateFactory(factory.DjangoModelFactory):
    carrier = factory.SubFactory(CarrierFactory)
    kind = models.CERTIFICATE_NO_WORKERS
    data = {
        "first_name": "Régis",
        "last_name": "Dujardin",
        "position": "Gérant",
        "location": "Saint André des Eaux",
    }

    class Meta:
        model = models.CarrierCertificate
