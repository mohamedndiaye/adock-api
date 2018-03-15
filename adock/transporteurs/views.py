import json

from django.http import JsonResponse
from django.utils import datastructures
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import models
from . import forms
from . import validators

TRANSPORTEUR_SEARCH_FIELDS = (
    'siret', 'raison_sociale', 'adresse', 'code_postal', 'ville',
    'telephone', 'email', 'code_ape', 'libelle_ape'
)

def get_transporteur_as_json(transporteur):
    transporteur_json = {}
    for field in TRANSPORTEUR_SEARCH_FIELDS:
        transporteur_json[field] = getattr(transporteur, field)
    return transporteur_json

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
    elif validators.RE_NOT_DIGIT.search(q):
        # The search criteria contains at least one not digit character so search on name
        transporteurs = models.Transporteur.objects.filter(raison_sociale__icontains=q)
    elif q_length == validators.SIREN_LENGTH:
        transporteurs = models.Transporteur.objects.filter(siret__startswith=q)
    elif q_length == validators.SIRET_LENGTH:
        transporteurs = models.Transporteur.objects.filter(siret=q)
    else:
        # Only digits but not SIREN or SIRET
        return JsonResponse({
            'message': "Le paramètre de recherche n'est pas valide."
        }, status=400)

    transporteurs_json = [
        get_transporteur_as_json(transporteur) for transporteur in transporteurs
    ]
    return JsonResponse({'results': transporteurs_json})

@csrf_exempt
@require_POST
def subscribe(request):
    payload = json.loads(request.body.decode("utf-8"))
    # Get existing transporteur if any
    transporteur = models.Transporteur.objects.filter(siret=payload['siret']).first()
    form = forms.SubscriptionForm(payload, instance=transporteur)
    if form.is_valid():
        transporteur = form.save()
        return JsonResponse({
            'id': transporteur.id,
        })
    else:
        return JsonResponse(form.errors, status=400)
