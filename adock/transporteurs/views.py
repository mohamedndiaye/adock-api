import json
import re

from django.conf import settings
from django.core.mail import mail_managers
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import datastructures, timezone
from django.views.decorators.csrf import csrf_exempt

from . import models
from . import forms
from . import validators

TRANSPORTEUR_LIST_FIELDS = (
    'siret', 'raison_sociale', 'adresse', 'code_postal', 'ville', 'completeness'
)

TRANSPORTEUR_DETAIL_FIELDS = (
    'siret', 'raison_sociale', 'adresse', 'code_postal', 'ville',
    'telephone', 'email',
    'debut_activite', 'code_ape', 'libelle_ape',
    'numero_tva', 'completeness',
    'lower_than_3_5_licenses', 'greater_than_3_5_licenses',
    'working_area', 'working_area_departements'
)

def get_transporteur_as_json(transporteur, fields):
    transporteur_json = {}
    for field in fields:
        if field == 'telephone' and not isinstance(transporteur.telephone, str):
            # Exception for PhoneNumberField
            value = '0' + transporteur.telephone.format_as(
                settings.PHONENUMBER_DEFAULT_REGION
            )
        else:
            value = getattr(transporteur, field)
        transporteur_json[field] = value
    return transporteur_json

def search(request):
    """The search allows partial SIRET or raison sociale"""
    try:
        q = request.GET['q']
    except datastructures.MultiValueDictKeyError:
        if len(request.GET) == 0:
            message = "La requête est vide."
        else:
            message = "Le paramêtre requis « q » n'a pas été trouvé."
        return JsonResponse({'message': message}, status=400)

    stripped_q = q.replace(' ', '')
    if validators.RE_NOT_DIGIT.search(stripped_q):
        # The search criteria contains at least one not digit character so search on name
        transporteurs = models.Transporteur.objects.filter(raison_sociale__icontains=q)
    else:
        transporteurs = models.Transporteur.objects.filter(siret__startswith=stripped_q)

    transporteurs = transporteurs.order_by('-completeness')
    transporteurs_json = [
        get_transporteur_as_json(transporteur, TRANSPORTEUR_LIST_FIELDS)
        for transporteur in transporteurs
    ]
    return JsonResponse({'results': transporteurs_json})


RE_MANY_COMMAS = re.compile(r',+')

@csrf_exempt
def transporteur_detail(request, transporteur_siret):
    # Get existing transporteur if any
    transporteur = get_object_or_404(models.Transporteur, siret=transporteur_siret)
    if request.method == 'PATCH':
        if not request.content_type == 'application/json':
            return JsonResponse(
                {'message': 'Seules les requêtes PATCH en JSON sont prises en charge.'},
                status=400
            )

        try:
            payload = json.loads(request.body.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            return JsonResponse(
                {'message': "Les données ne sont pas valides."},
                status=400
            )

        # Replace all non digits by ',' and avoid duplicates ','
        cleaned_departements = payload.get('working_area_departements')
        if cleaned_departements:
            cleaned_departements = cleaned_departements.replace(' ', ',')
            payload['working_area_departements'] = RE_MANY_COMMAS.sub(',', cleaned_departements)
        form = forms.SubscriptionForm(payload, instance=transporteur)
        if not form.is_valid():
            return JsonResponse(form.errors, status=400)

        # Valid
        transporteur = form.save(commit=False)
        transporteur.validated_at = timezone.now()
        transporteur.save()

        # Send a mail to managers to track changes
        subject = "Modification du transporteur {0}".format(transporteur.siret)
        message = """
            Modification du transporteur : {raison_sociale}
            SIRET : {siret}

            Nouveaux champs :
            - téléphone « {telephone} »
            - adresse électronique « {email} »
            - zone de travail « {working_area} »
            - départements livrés « {working_area_departements} »
        """.format(
            raison_sociale=transporteur.raison_sociale,
            siret=transporteur.siret,
            telephone=transporteur.telephone,
            email=transporteur.email,
            working_area=transporteur.get_working_area_display(),
            working_area_departements=transporteur.working_area_departements
        )
        mail_managers(subject, message, fail_silently=True)

    transporteur_as_json = get_transporteur_as_json(transporteur, TRANSPORTEUR_DETAIL_FIELDS)
    return JsonResponse(transporteur_as_json)
