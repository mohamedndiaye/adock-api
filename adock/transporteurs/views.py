import json
import re

from django.conf import settings
from django.core.mail import mail_managers
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from . import models
from . import forms
from . import validators

TRANSPORTEUR_LIST_FIELDS = (
    'siret', 'raison_sociale', 'adresse', 'code_postal', 'ville', 'completeness'
)

TRANSPORTEUR_DETAIL_FIELDS = (
    'siret', 'raison_sociale', 'gestionnaire',
    'adresse', 'code_postal', 'ville',
    'telephone', 'email',
    'debut_activite', 'code_ape', 'libelle_ape',
    'numero_tva', 'completeness',
    'lti_numero', 'lti_date_debut', 'lti_date_fin', 'lti_nombre',
    'lc_numero', 'lc_date_debut', 'lc_date_fin', 'lc_nombre',
    'working_area', 'working_area_departements',
    'specialities'
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
    """The search allows to filter on:
       - partial raison sociale or SIRET
       - type of the license (LC heavy or LTI light)
    """
    transporteurs = models.Transporteur.objects.all()

    q = request.GET.get('q')
    if q:
        # Filtering on raison sociale or SIRET
        q = q.upper()
        stripped_q = q.replace(' ', '')
        if validators.RE_NOT_DIGIT.search(stripped_q):
            # The search criteria contains at least one not digit character so search on name
            transporteurs = transporteurs.filter(raison_sociale__contains=q)
        else:
            transporteurs = transporteurs.filter(siret__startswith=stripped_q)

    # Filtering on type of license
    license_types = request.GET.getlist('licence-types[]')
    for license_type in license_types:
        if license_type == 'lc':
            transporteurs = transporteurs.exclude(lc_numero='')
        elif license_type == 'lti':
            transporteurs = transporteurs.exclude(lti_numero='')

    # Filtering on departements
    departements = []
    for field in ('departement-depart', 'departement-arrivee'):
        departement = request.GET.get(field)
        if departement:
            try:
                departement = int(departement)
                if 0 < departement and departement < 1000:
                    departements.append(departement)
            except ValueError:
                message = "Le numéro de département « %s » est non valide." % request.GET.get(field)
                return JsonResponse({'message': message}, status=400)

    if departements:
        transporteurs = transporteurs.filter(
            Q(working_area=models.WORKING_AREA_FRANCE) |
            Q(working_area=models.WORKING_AREA_DEPARTEMENT, working_area_departements__contains=departements)
        )

    # Filtering on specialities
    specialities = request.GET.getlist('specialities[]')
    if specialities:
        transporteurs = transporteurs.filter(specialities__contains=specialities)

    transporteurs = (transporteurs
        .order_by('raison_sociale', '-completeness')
        .values(*TRANSPORTEUR_LIST_FIELDS)
        [:settings.TRANSPORTEURS_LIMIT])

    payload = {
        'results': list(transporteurs)
    }
    if len(payload['results']) == settings.TRANSPORTEURS_LIMIT:
        payload['limit'] = settings.TRANSPORTEURS_LIMIT
    return JsonResponse(payload)

def get_transporteur_changes(transporteur, cleaned_payload):
    old_data = {field: getattr(transporteur, field) for field in cleaned_payload}
    old_data_changed = {}
    for k, v in old_data.items():
        if v != cleaned_payload[k]:
            # Serialize for JSON
            old_data_changed[k] = str(v)

    return old_data_changed

def mail_managers_changes(transporteur, old_data_changed):
    # Send a mail to managers to track changes
    subject = "Modification du transporteur {0}".format(transporteur.siret)
    message = """
Modification du transporteur : {raison_sociale}
SIRET : {siret}
https://{website}{transporteur_url}

Valeurs modifiées :
    """.format(
        raison_sociale=transporteur.raison_sociale,
        siret=transporteur.siret,
        website=settings.WEBSITE,
        transporteur_url=transporteur.get_absolute_url()
    )

    for field, old_value in old_data_changed.items():
        message += "\n- {field} : {old_value} => {new_value}".format(
            field=field,
            old_value=old_value,
            new_value=getattr(transporteur, field)
        )
    mail_managers(subject, message, fail_silently=True)


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

        # Form is not bound to the transporteur instance
        form = forms.SubscriptionForm(payload)
        if not form.is_valid():
            return JsonResponse(form.errors, status=400)

        # Valid
        cleaned_payload = {k: form.cleaned_data[k] for k in payload.keys()}

        old_data_changed = get_transporteur_changes(transporteur, cleaned_payload)
        if old_data_changed:
            # Data has been modified so saving is required
            # Don't use form.save to edit only the submitted fields of the instance
            updated_fields = old_data_changed.keys()
            for field in updated_fields:
                setattr(transporteur, field, cleaned_payload[field])
            transporteur.validated_at = timezone.now()

            with transaction.atomic(savepoint=False):
                transporteur.save(
                    force_update=True,
                    update_fields=updated_fields
                )
                models.TransporteurLog.objects.create(transporteur=transporteur, data=old_data_changed)

            mail_managers_changes(transporteur, old_data_changed)

    transporteur_as_json = get_transporteur_as_json(transporteur, TRANSPORTEUR_DETAIL_FIELDS)
    return JsonResponse(transporteur_as_json)
