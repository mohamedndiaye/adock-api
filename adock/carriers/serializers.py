# pylint: disable=W0223
from rest_framework import serializers

from ..accounts import models as accounts_models
from . import validators as carriers_validators
from . import models as carriers_models


class CreatedByEmailSerializer(serializers.Serializer):
    created_by_email = serializers.EmailField(
        max_length=255, allow_blank=True, required=False
    )

    def __init__(self, *args, **kwargs):
        self.created_by = None
        super().__init__(*args, **kwargs)

    def validate_created_by_email(self, value):
        if value:
            try:
                # Only possible for inactive accounts
                self.created_by = accounts_models.User.objects.get(
                    email=value, is_active=False
                )
            except accounts_models.User.DoesNotExist:
                raise serializers.ValidationError(
                    "L'adresse électronique n'est pas valide."
                )

        return value


class CarrierEditableSerializer(serializers.ModelSerializer):
    class Meta:
        model = carriers_models.CarrierEditable
        fields = (
            "description",
            "email",
            "specialities",
            "telephone",
            "website",
            "working_area_departements",
            "working_area",
        )

    def validate_telephone(self, value):
        # Validated by phonenumber before
        if not value:
            raise serializers.ValidationError("Ce champ ne peut être vide.")
        return value

    def validate_working_area_departements(self, value):
        """Pads departement numbers lesser than 10 with a zero"""
        formated_departements = []
        for departement in value:
            formated_departements.append("{:0>2}".format(departement))

        # Unique and sorted
        return sorted(set(formated_departements))

    def validate_website(self, value):
        return carriers_validators.validate_scheme(value)

    def validate(self, attrs):
        if attrs.get(
            "working_area"
        ) == carriers_models.WORKING_AREA_DEPARTEMENT and not attrs.get(
            "working_area_departements", []
        ):
            raise serializers.ValidationError(
                {
                    "working_area_departements": "Des départements doivent être "
                    "renseignés quand l'aire de travail est départementale."
                }
            )
        return attrs


class WorkerSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    date = serializers.CharField(max_length=64)
    nationality = serializers.CharField(max_length=64)
    work_permit = serializers.CharField(max_length=64)


class CertificateSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(
        required=True, choices=carriers_models.CERTIFICATE_CHOICES
    )
    last_name = serializers.CharField(max_length=100)
    first_name = serializers.CharField(max_length=100)
    position = serializers.CharField(max_length=100)
    location = serializers.CharField(max_length=100)
    workers = WorkerSerializer(required=False, many=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial_data["kind"] == carriers_models.CERTIFICATE_WORKERS:
            self.fields["workers"].required = True


class LicenseRenewalSerializer(serializers.Serializer):
    # 0 or None are ignored
    lti_nombre = serializers.IntegerField(min_value=0, default=0, required=False)
    lc_nombre = serializers.IntegerField(min_value=0, default=0, required=False)

    def validate(self, attrs):
        if not attrs.get("lti_nombre") and not attrs.get("lc_nombre"):
            raise serializers.ValidationError(
                {
                    "__all__": "Au moins, un nombre de license LTI ou LC doit être renseigné."
                }
            )
        return attrs
