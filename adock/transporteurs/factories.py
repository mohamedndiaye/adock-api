import datetime
import factory
from factory import fuzzy
import random
import string

from . import models
from . import validators

def get_license_number(o, n):
    keys = ['82', '84', '93']
    return "{} {} {:0>8}".format(
        o.lti_date_debut.year,
        random.choice(keys),
        n
    )

class TransporteurFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Transporteur

    siret = fuzzy.FuzzyText(length=validators.SIRET_LENGTH, chars=string.digits)
    categorie_juridique = "Société par actions simplifiée (SAS)"
    raison_sociale = factory.Faker('company', locale='fr_FR')
    adresse = factory.Faker('street_address', locale='fr_FR')
    code_postal = factory.Faker('zipcode')
    ville = factory.Faker('city')
    telephone = factory.Faker('phone_number', locale='fr_FR')
    email = factory.Faker('email', locale='fr_FR')
    date_creation = fuzzy.FuzzyDate(datetime.date(1950, 1, 1))
    debut_activite = factory.LazyAttribute(lambda o: o.date_creation)
    code_ape = '4941A'
    libelle_ape = 'Transports routiers de fret interurbains'
    gestionnaire = factory.Faker('name')
    working_area = models.WORKING_AREA_DEPARTEMENT
    working_area_departements = [35, 44]
    lti_numero = factory.LazyAttributeSequence(get_license_number)
    lti_date_debut = fuzzy.FuzzyDate(datetime.date(2015, 1, 1))
    lti_date_fin = factory.LazyAttribute(
        lambda o: o.lti_date_debut + datetime.timedelta(days=6*364))
    lti_nombre = fuzzy.FuzzyInteger(1, 20)
