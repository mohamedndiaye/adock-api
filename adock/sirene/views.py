import re

from django.http import JsonResponse
from django.utils import datastructures

from . import models as sirene_models

SIREN_LENGTH = 9
SIRET_LENGTH = 14

RE_NOT_DIGIT = re.compile(r'\D')

def serialize_company(company):
    return {
        'siret': company.get_siret(),
        'l1_normalisee': company.l1_normalisee
    }

def search(request):
    try:
        q = request.GET['q']
    except datastructures.MultiValueDictKeyError:
        if len(request.GET) == 0:
            message = 'Empty query.'
        else:
            message = 'Required parameter not found.'
        return JsonResponse({
            'message': message
        }, status=400)

    # Allows SIREN instead of SIRET
    q_length = len(q)
    if q_length <= 0:
        return JsonResponse({
            'message': 'Empty search query.'
        }, status=400)
    elif RE_NOT_DIGIT.search(q):
        # The search criteria contains at least one not digit character so search on name
        companies = sirene_models.Sirene.objects.filter(l1_normalisee__icontains=q)
    elif q_length == SIREN_LENGTH:
        companies = sirene_models.Sirene.objects.filter(siren=q)
    elif q_length == SIRET_LENGTH:
        companies = sirene_models.Sirene.objects.filter(siren=q[:SIREN_LENGTH], nic=q[SIREN_LENGTH:])
    else:
        # Only digits but not SIREN or SIRET
        return JsonResponse({
            'message': 'Invalid search query.'
        }, status=400)

    companies_json = [serialize_company(company) for company in companies]
    return JsonResponse({'results': companies_json})
