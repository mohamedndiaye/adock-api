import re

from django.http import JsonResponse
from django.utils import datastructures

from . import models as sirene_models

SIREN_LENGTH = 9
SIRET_LENGTH = 14

RE_NOT_DIGIT = re.compile(r'\D')

def serialize_entreprise(entreprise):
    return {
        'siret': entreprise.get_siret(),
        'l1_normalisee': entreprise.l1_normalisee
    }

def search(request):
    try:
        q = request.GET['q']
    except datastructures.MultiValueDictKeyError:
        if len(request.GET) == 0:
            message = "La requête est vide."
        else:
            message = "Le paramêtre requis « q » n'a pas été trouvé."
        return JsonResponse({
            'message': message
        }, status=400)

    # Allows SIREN instead of SIRET
    q_length = len(q)
    if q_length <= 0:
        return JsonResponse({
            'message': "Le paramètre de recherche est vide."
        }, status=400)
    elif RE_NOT_DIGIT.search(q):
        # The search criteria contains at least one not digit character so search on name
        entreprises = sirene_models.Sirene.objects.filter(l1_normalisee__icontains=q)
    elif q_length == SIREN_LENGTH:
        entreprises = sirene_models.Sirene.objects.filter(siren=q)
    elif q_length == SIRET_LENGTH:
        entreprises = sirene_models.Sirene.objects.filter(siren=q[:SIREN_LENGTH], nic=q[SIREN_LENGTH:])
    else:
        # Only digits but not SIREN or SIRET
        return JsonResponse({
            'message': "Le paramètre de recherche n'est pas valide."
        }, status=400)

    entreprises_json = [serialize_entreprise(entreprise) for entreprise in entreprises]
    return JsonResponse({'results': entreprises_json})
