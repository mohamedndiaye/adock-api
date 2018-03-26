import datetime
import factory
from factory import fuzzy
import string

from . import models
from . import validators


class TransporteurFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Transporteur

    siret = fuzzy.FuzzyText(length=validators.SIRET_LENGTH, chars=string.digits)
    raison_sociale = factory.Faker('company', locale='fr_FR')
    adresse = factory.Faker('street_address', locale='fr_FR')
    code_postal = factory.Faker('zipcode')
    telephone = factory.Faker('phone_number', locale='fr_FR')
    email = factory.Faker('email', locale='fr_FR')
    date_creation = fuzzy.FuzzyDate(datetime.date(1950, 1, 1))
    debut_activite = factory.LazyAttribute(lambda o: o.date_creation)
    code_ape = '4941A'
    libelle_ape = 'Transports routiers de fret interurbains'
    working_area = models.WORKING_AREA_DEPARTEMENT
    working_area_departements = [35, 44]
