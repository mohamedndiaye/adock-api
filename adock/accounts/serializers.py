# pylint: disable=W0223
from rest_framework import serializers
from django.contrib.auth import password_validation

from . import models as accounts_models
from . import tokens as accounts_tokens


class CreateAccountSerializer(serializers.Serializer):
    """Don't use ModelSerializer to require some fields not required in model."""

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

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value


class EditUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = accounts_models.User
        fields = ("has_accepted_cgu",)

    def validate_has_accepted_cgu(self, value):
        if not value:
            raise serializers.ValidationError("L'acceptation des CGU est irréversible.")
        return value

    def update(self, instance, validated_data):
        instance.has_accepted_cgu = validated_data["has_accepted_cgu"]
        instance.save(update_fields=["has_accepted_cgu"])
        return instance


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    token = serializers.CharField(max_length=64)
    password = serializers.CharField(min_length=8)

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate(self, attrs):
        try:
            # Store the user for future use
            attrs["user"] = accounts_models.User.objects.get(
                email=attrs["email"],
                provider=accounts_models.PROVIDER_A_DOCK,
                is_active=True,
            )
        except accounts_models.User.DoesNotExist:
            return serializers.ValidationError("L'utilisateur n'existe pas.")

        if not accounts_tokens.account_activation_token.check_token(
            attrs["user"], attrs["token"]
        ):
            return serializers.ValidationError(
                "Le jeton d'activation n'est pas valide."
            )

        return attrs
