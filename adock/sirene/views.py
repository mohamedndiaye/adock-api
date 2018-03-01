from django.db import connection
from django.http import JsonResponse
from django.utils import datastructures

SIREN_LENGTH = 9
SIRET_LENGTH = 14


def search(request):
    try:
        raw_siren = request.GET['siren']
    except datastructures.MultiValueDictKeyError:
        return JsonResponse({
            'message': 'Empty query.'
        }, status=400)

    # Allows SIREN instead of SIRET
    nic = None
    raw_siren_length = len(raw_siren)
    if raw_siren_length == SIREN_LENGTH:
        siren = raw_siren
    elif raw_siren_length == SIRET_LENGTH:
        siren = raw_siren[:SIREN_LENGTH]
        nic = raw_siren[SIREN_LENGTH:]
    else:
        return JsonResponse({
            'message': 'Invalid SIREN/SIRET'
        }, status=400)

    with connection.cursor() as cursor:
        # Raw SQL to avoid model definition in this POC
        query = "SELECT * FROM sirene WHERE siren = %s"
        params = [siren]
        if nic:
            query += " AND nic = %s"
            params.append(nic)

        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        companies = [dict(zip(columns, company)) for company in cursor.fetchall()]

    return JsonResponse({'results': companies})

