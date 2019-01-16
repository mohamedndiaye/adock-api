from rest_framework import serializers


class WorkerSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, allow_blank=False, max_length=100)
    date = serializers.CharField(required=True, allow_blank=False, max_length=64)
    nationality = serializers.CharField(required=True, allow_blank=False, max_length=64)
    work_permit = serializers.CharField(required=True, allow_blank=False, max_length=64)


class CertificateSerializer(serializers.Serializer):
    last_name = serializers.CharField(required=True, allow_blank=False, max_length=100)
    first_name = serializers.CharField(required=True, allow_blank=False, max_length=100)
    position = serializers.CharField(required=True, allow_blank=False, max_length=100)
    location = serializers.CharField(required=True, allow_blank=False, max_length=100)


class CertificateWithWorkersSerializer(CertificateSerializer):
    workers = WorkerSerializer(many=True)
