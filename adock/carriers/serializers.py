# pylint: disable=W0223
from rest_framework import serializers

from . import models as carriers_models


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
