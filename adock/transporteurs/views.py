import json
import re

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Q
from django.db.models.expressions import OrderBy, RawSQL
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from . import forms
from . import mails
from . import models
from . import tokens
from . import validators

TRANSPORTEUR_LIST_FIELDS = (
    'siret', 'raison_sociale', 'enseigne', 'adresse', 'code_postal', 'ville',
    'completeness', 'lti_nombre', 'lc_nombre', 'working_area'
)

TRANSPORTEUR_DETAIL_FIELDS = (
    'siret', 'raison_sociale', 'enseigne', 'gestionnaire',
    'adresse', 'code_postal', 'ville',
    'telephone', 'email',
    'debut_activite', 'code_ape', 'libelle_ape',
    'numero_tva', 'completeness',
    'lti_numero', 'lti_date_debut', 'lti_date_fin', 'lti_nombre',
    'lc_numero', 'lc_date_debut', 'lc_date_fin', 'lc_nombre',
    'working_area', 'working_area_departements',
    'specialities', 'website', 'description',
    'in_sirene', 'deleted_at',
    # Boolean for real email_confirmed_at field to avoid privacy issue
    'is_locked'
)

def get_transporteur_as_json(transporteur, fields):
    transporteur_json = {}
    for field in fields:
        if field == 'telephone' and not isinstance(transporteur.telephone, str):
            # Exception for PhoneNumberField
            value = '0' + transporteur.telephone.format_as(
                settings.PHONENUMBER_DEFAULT_REGION
            )
        elif field == 'is_locked':
            value = bool(transporteur.email_confirmed_at)
        else:
            value = getattr(transporteur, field)

        transporteur_json[field] = value
    return transporteur_json

def get_transporteur_subsidiaries_as_json(transporteur):
    subsidiaries = (
        models.Transporteur.objects
        .filter(siret__startswith=transporteur.siret[:validators.SIREN_LENGTH])
        .exclude(pk=transporteur.pk)
        .values('siret', 'code_postal', 'ville', 'debut_activite', 'is_siege')
    )
    return list(subsidiaries)

def search(request):
    """The search allows to filter on:
       - partial enseigne or SIRET
       - type of the license (LC heavy or LTI light)
    """
    transporteurs = models.Transporteur.objects.filter(deleted_at=None)
    q = request.GET.get('q')
    if q:
        # Filtering on enseigne or SIRET
        q = q.upper()
        criteria_list = q.split(',')
        for criteria in criteria_list:
            criteria = criteria.strip()
            if validators.RE_NOT_DIGIT_ONLY.search(criteria):
                # Dynamic unaccent is too slow (237x slower!) so we created a dedicated field
                # in DB and use raw SQL too avoid useless replaces added by the ORM.
                # The search criteria contains at least one not digit character so search on name
                transporteurs = transporteurs.filter(enseigne_unaccent__ucontains=criteria)
            else:
                # criteria contains only digits
                if len(criteria) > 5:
                    # SIREN is longer than 5
                    transporteurs = transporteurs.filter(siret__startswith=criteria)
                else:
                    # Zip code are shorter than 5 digits, could be a digit in
                    # the company name too (limited to 5). Criteria contains
                    # only digits so the filtering will return same results
                    # against enseigne and enseigne_unaccent, however it's
                    # better to compare against enseigne_unaccent to reduce the
                    # number of DB indexes.
                    transporteurs = transporteurs.filter(
                        Q(code_postal__startswith=criteria) |
                        Q(enseigne_unaccent__contains=criteria)
                    )

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
            if validators.is_french_departement(departement):
                departements.append(departement)
            else:
                message = "Le numéro de département français « %s » n'est pas valide." % request.GET.get(field)
                return JsonResponse({'message': message}, status=400)

    if departements:
        transporteurs = transporteurs.filter(
            Q(working_area=models.WORKING_AREA_INTERNATIONAL) |
            Q(working_area=models.WORKING_AREA_FRANCE) |
            Q(working_area=models.WORKING_AREA_DEPARTEMENT, working_area_departements__contains=departements)
        )

    # Filtering on specialities
    specialities = request.GET.getlist('specialities[]')
    if specialities:
        transporteurs = transporteurs.filter(specialities__contains=specialities)

    # Ordering

    # Raw SQL is more simple here than Case, When, etc
    order_departement_counter = OrderBy(
        RawSQL("""
            CASE working_area
            WHEN 'DEPARTEMENT' THEN array_length(working_area_departements, 1)
            WHEN 'FRANCE' THEN 101
            WHEN 'INTERNATIONAL' THEN 102
            END
        """, ()),
        nulls_last=True
    )

    order_by_list = [
        order_departement_counter,
    ]

    # By departement of the company if relevant
    if departements:
        order_departement_company = RawSQL(
            "CASE WHEN departement IN (%s) THEN 1 ELSE 2 END",
            (','.join(departements),)
        )
        order_by_list.append(order_departement_company)

    # By completeness and enseigne
    order_by_list.extend((
        '-completeness',
        'enseigne'
    ))
    transporteurs = (
        transporteurs
        .order_by(*order_by_list)
        .values(*TRANSPORTEUR_LIST_FIELDS)
        [:settings.TRANSPORTEURS_LIMIT]
    )

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


RE_MANY_COMMAS = re.compile(r',+')

@csrf_exempt
def transporteur_detail(request, transporteur_siret):
    response_json = {}
    # Access to deleted transporteurs is allowed.
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
        raw_departements = payload.get('working_area_departements')
        if raw_departements:
            raw_departements = raw_departements.replace(' ', ',')
            payload['working_area_departements'] = RE_MANY_COMMAS.sub(',', raw_departements)

        # Form is not bound to the transporteur instance but we need it to check edit code
        form = forms.SubscriptionForm(payload, transporteur=transporteur)
        if not form.is_valid():
            return JsonResponse(form.errors, status=400)

        # Exclude edit code from changes if not up to you to define it!
        form.cleaned_data.pop('edit_code')

        # Limit cleaned_data to the keys of the payload but only accept keys of cleaned_data (intersection)
        # to only update the submitted values
        cleaned_payload = {k: form.cleaned_data[k] for k in payload.keys() if k in form.cleaned_data}

        # Only set in PATCH request
        confirmation_email_to_send = False
        scheme = 'https' if request.is_secure() else 'http'

        # Special case when the user validates (first time) the already known email address
        if transporteur.validated_at is None and transporteur.email:
            confirmation_email_to_send = True

        # Only apply the submitted values if they are different in DB
        old_data_changed = get_transporteur_changes(transporteur, cleaned_payload)
        if old_data_changed:
            # Data has been modified so saving is required
            # Don't use form.save to edit only the submitted fields of the instance
            updated_fields = list(old_data_changed.keys())

            for field in updated_fields:
                setattr(transporteur, field, cleaned_payload[field])

            with transaction.atomic(savepoint=False):
                transporteur.validated_at = timezone.now()
                updated_fields.append('validated_at')

                if 'email' in updated_fields:
                    # New email should invalidate email confirmation and edit code
                    transporteur.email_confirmed_at = None
                    transporteur.edit_code = None
                    transporteur.edit_code_at = None
                    updated_fields.extend(['email_confirmed_at', 'edit_code', 'edit_code_at'])
                    confirmation_email_to_send = True

                transporteur.save(
                    force_update=True,
                    update_fields=updated_fields
                )
                models.TransporteurLog.objects.create(transporteur=transporteur, data=old_data_changed)

            mails.mail_managers_changes(transporteur, old_data_changed, scheme)

        if confirmation_email_to_send:
            mails.mail_transporteur_to_confirm_email(transporteur, scheme)

        response_json['confirmation_email_sent'] = confirmation_email_to_send

    transporteur_json = get_transporteur_as_json(transporteur, TRANSPORTEUR_DETAIL_FIELDS)
    transporteur_json['subsidiaries'] = get_transporteur_subsidiaries_as_json(transporteur)
    response_json['transporteur'] = transporteur_json
    return JsonResponse(response_json)

def transporteur_confirm_email(request, transporteur_siret, token):
    try:
        transporteur = models.Transporteur.objects.get(pk=transporteur_siret)
    except models.Transporteur.DoesNotExist:
        transporteur = None

    if transporteur and tokens.email_confirmation_token.check_token(transporteur, token):
        transporteur.email_confirmed_at = timezone.now()
        transporteur.save()
        return JsonResponse(
            {'message': "L'adresse électronique est confirmée."}
        )

    return JsonResponse(
        {'message': "Impossible de confirmer l'adresse électronique."},
        status=400
    )


def transporteur_send_edit_code(request, transporteur_siret):
    transporteur = get_object_or_404(models.Transporteur, siret=transporteur_siret)

    if not transporteur.is_locked():
        return JsonResponse(
            {'message': "L'adresse électronique n'est pas confirmée."},
            status=409
        )

    if transporteur.edit_code_has_expired():
        transporteur.set_edit_code()
        transporteur.save()
        mails.mail_transporteur_edit_code(transporteur)
        message = "Un code de modification a été envoyé par courriel."
        status = 201
    else:
        message = "Le précédent code de modification envoyé est toujours valide."
        status = 200

    return JsonResponse(
        {
            'message': message,
            'email': transporteur.email,
            'edit_code_at': transporteur.edit_code_at,
            'edit_code_timeout_at': transporteur.get_edit_code_timeout_at()
        },
        status=status
    )

def get_stats(request):
    validated_carriers_per_month = []
    with connection.cursor() as cursor:
        # Collect the number of validated sheets by month.
        # A bit slow, 18ms...
        cursor.execute("""
            SELECT
                gs.generated_month::date,
                count(t.siret)
            FROM
                (SELECT date_trunc('month', calendar.date) as generated_month
                FROM generate_series(
                        now() - interval '6 month',
                        now() - interval '1 month',
                        interval '1 month') AS calendar(date)) gs
                LEFT JOIN transporteur t
                    ON t.validated_at is not null AND
                        date_trunc('month', t.validated_at) = generated_month
            GROUP BY generated_month
            ORDER BY generated_month""")
        for row in cursor.fetchall():
            validated_carriers_per_month.append(
                {
                    'month': row[0],
                    'count': row[1]
                }
            )

    # Number of locked sheets
    confirmed_carriers = models.Transporteur.objects.filter(email_confirmed_at__isnull=False).count()
    return JsonResponse({
        'validated_carriers_per_month': validated_carriers_per_month,
        'confirmed_carriers': confirmed_carriers
    })
