from django.contrib.auth import get_user_model

import factory
from faker import Faker


faker = Faker("fr_FR")


class UserFactory(factory.django.DjangoModelFactory):
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'secret')

    class Meta:
        model = get_user_model()
