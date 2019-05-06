# pylint: disable=W0223
from rest_framework import serializers

from . import models as carriers_models


class CarrierEditableSerializer(serializers.ModelSerializer):
    class Meta:
        model = carriers_models.CarrierEditable
        fields = (
            "telephone",
            "email",
            "working_area",
            "working_area_departements",
            "specialities",
            "website",
            "description",
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
        # Tied to LooseURLValidator
        if not value.startswith("http://") and not value.startswith("https://"):
            value = "http://" + value
        return value

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
