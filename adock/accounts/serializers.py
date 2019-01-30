# pylint: disable=W0223
from rest_framework import serializers

from . import models as accounts_models


class CreateAccountSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=8)

    def validate_email(self, value):
        if accounts_models.User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Un compte utilisateur existe déjà avec cette adresse."
            )
        return value
