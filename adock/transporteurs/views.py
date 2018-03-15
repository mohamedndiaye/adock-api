import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import datastructures
from django.views.decorators.csrf import csrf_exempt

from . import models
from . import forms
from . import validators

TRANSPORTEUR_LIST_FIELDS = (
    'siret', 'raison_sociale', 'adresse', 'code_postal', 'ville'
)

TRANSPORTEUR_DETAIL_FIELDS = (
    'siret', 'raison_sociale', 'adresse', 'code_postal', 'ville',
    'telephone', 'email',
    'debut_activite', 'code_ape', 'libelle_ape',
    'lower_than_3_5_licenses', 'greater_than_3_5_licenses'
)

def get_transporteur_as_json(transporteur, fields):
    transporteur_json = {}
    for field in fields:
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
        get_transporteur_as_json(transporteur, TRANSPORTEUR_LIST_FIELDS) for transporteur in transporteurs
    ]
    return JsonResponse({'results': transporteurs_json})

@csrf_exempt
def transporteur_detail(request, transporteur_siret):
    # Get existing transporteur if any
    transporteur = get_object_or_404(models.Transporteur, siret=transporteur_siret)
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            return JsonResponse({
                'message': "Les données ne sont pas valides.",
            }, status=400)

        form = forms.SubscriptionForm(payload, instance=transporteur)
        if not form.is_valid():
            return JsonResponse(form.errors, status=400)
        # Valid
        transporteur = form.save()

    transporteur_as_json = get_transporteur_as_json(transporteur, TRANSPORTEUR_DETAIL_FIELDS)
    return JsonResponse(transporteur_as_json)
