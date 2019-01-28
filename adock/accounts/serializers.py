# pylint: disable=W0223
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from . import models as accounts_models


class AccountSerializer(serializers.Serializer):
    last_name = serializers.CharField(max_length=100)
    first_name = serializers.CharField(max_length=100)
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=accounts_models.User.objects.all(),
                message="Un utilisateur avec cette adresse existe déjà.",
            )
        ]
    )
    password = serializers.CharField(min_length=8)
