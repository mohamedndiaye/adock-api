import factory
from faker import Faker

from . import models

faker = Faker("fr_FR")


class UserFactory(factory.django.DjangoModelFactory):
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'secret')

    class Meta:
        model = models.User
