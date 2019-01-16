import json

from django.http import JsonResponse
from rest_framework import serializers


def request_load(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.decoder.JSONDecodeError:
        return (
            None,
            JsonResponse({"message": "Les données ne sont pas valides."}, status=400),
        )

    return payload, None


def request_validate(request, Serializer):
    payload, response = request_load(request)
    if response:
        return None, response

    serializer = Serializer(data=payload)
    try:
        serializer.is_valid(raise_exception=True)
    except serializers.ValidationError:
        return None, JsonResponse(serializer.errors, status=400)

    return serializer, None
