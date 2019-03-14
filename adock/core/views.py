import json

from django.http import JsonResponse
from rest_framework import serializers


def request_load(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.decoder.JSONDecodeError:
        return (
            None,
            JsonResponse(
                {"message": "Le format des données n'est pas valide."}, status=400
            ),
        )

    return payload, None


def request_validate(request, Serializer, instance=None):
    payload, response = request_load(request)
    if response:
        return None, response

    serializer = Serializer(instance=instance, data=payload)
    try:
        serializer.is_valid(raise_exception=True)
    except serializers.ValidationError:
        # Workaround strange error format of DRF for Array
        errors = {}
        for k_field, v_error in serializer.errors.items():
            if isinstance(v_error, dict):
                errors[k_field] = [
                    "Champ %s : %s" % (int(k) + 1, ",".join(v))
                    for k, v in v_error.items()
                ]
            else:
                errors[k_field] = v_error
        return None, JsonResponse({"errors": errors}, status=400)

    return serializer, None
