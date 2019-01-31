import re

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.db.models.expressions import OrderBy, RawSQL
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.formats import date_format
import sentry_sdk

from adock.core import pdf as core_pdf
from adock.core import views as core_views

from . import forms, mails, models, tokens, validators
from . import serializers as carriers_serializers

CARRIER_LIST_FIELDS = (
    "siret",
    "raison_sociale",
    "enseigne",
    "adresse",
    "code_postal",
    "ville",
    "completeness",
    "lti_nombre",
    "lc_nombre",
    "working_area",
)

CARRIER_DETAIL_FIELDS = (
    "siret",
    "raison_sociale",
    "enseigne",
    "gestionnaire",
    "adresse",
    "code_postal",
    "ville",
    "telephone",
    # "email" is added when the carrier is validated (not locked)
    "debut_activite",
    "code_ape",
    "libelle_ape",
    "numero_tva",
    "completeness",
    "lti_numero",
    "lti_date_debut",
    "lti_date_fin",
    "lti_nombre",
    "lc_numero",
    "lc_date_debut",
    "lc_date_fin",
    "lc_nombre",
    "working_area",
    "working_area_departements",
    "specialities",
    "website",
    "description",
    "objectif_co2",
    "objectif_co2_begin",
    "objectif_co2_end",
    "deleted_at",
    "sirene_deleted_at",
    # Boolean for real email_confirmed_at field to avoid privacy issue
    "is_locked",
    "longitude",
    "latitude",
)

OTHER_FACILITIES_LIST_FIELDS = (
    "code_postal",
    "completeness",
    "debut_activite",
    "deleted_at",
    "enseigne",
    "is_siege",
    "sirene_deleted_at",
    "siret",
    "ville",
)


def get_carrier_as_json(carrier, fields):
    carrier_json = {}
    for field in fields:
        if field == "telephone" and not isinstance(carrier.telephone, str):
            # Exception for PhoneNumberField
            value = "0" + carrier.telephone.format_as(
                settings.PHONENUMBER_DEFAULT_REGION
            )
        elif field == "is_locked":
            value = bool(carrier.email_confirmed_at)
        else:
            value = getattr(carrier, field)

        carrier_json[field] = value
    return carrier_json


def get_other_facilities_as_json(carrier):
    other_facilities = (
        models.Carrier.objects.filter(
            siret__startswith=carrier.siret[: validators.SIREN_LENGTH]
        )
        .exclude(pk=carrier.pk)
        .values(*OTHER_FACILITIES_LIST_FIELDS)
    )
    return list(other_facilities)


def get_latest_certificate_as_json(carrier):
    certificate = carrier.get_latest_certificate()
    if not certificate:
        return None

    return {
        "kind_display": certificate.get_kind_display(),
        "created_at": certificate.created_at,
    }


def carrier_search(request):
    """The search allows to filter on:
       - partial enseigne or SIRET
       - type of the license (LC heavy or LTI light)
    """
    carriers = models.Carrier.objects.filter(deleted_at=None, sirene_deleted_at=None)
    q = request.GET.get("q")
    if q:
        # Filtering on enseigne or SIRET
        q = q.upper()
        criteria_list = q.split(",")
        for criteria in criteria_list:
            criteria = criteria.strip()
            if validators.RE_NOT_DIGIT_ONLY.search(criteria):
                # Dynamic unaccent is too slow (237x slower!) so we created a dedicated field
                # in DB and use raw SQL too avoid useless replaces added by the ORM.
                # The search criteria contains at least one not digit character so search on name
                carriers = carriers.filter(enseigne_unaccent__ucontains=criteria)
            else:
                # criteria contains only digits
                if len(criteria) > 5:
                    # SIREN is longer than 5
                    carriers = carriers.filter(siret__startswith=criteria)
                else:
                    # Zip code are shorter than 5 digits, could be a digit in
                    # the company name too (limited to 5). Criteria contains
                    # only digits so the filtering will return same results
                    # against enseigne and enseigne_unaccent, however it's
                    # better to compare against enseigne_unaccent to reduce the
                    # number of DB indexes.
                    carriers = carriers.filter(
                        Q(code_postal__startswith=criteria)
                        | Q(enseigne_unaccent__contains=criteria)
                    )

    # Filtering on type of license
    license_types = request.GET.getlist("licence-types[]")
    for license_type in license_types:
        if license_type == "lc":
            carriers = carriers.exclude(lc_numero="")
        elif license_type == "lti":
            carriers = carriers.exclude(lti_numero="")

    # Filtering on departements
    departements = []
    for field in ("departement-depart", "departement-arrivee"):
        departement = request.GET.get(field)
        if departement:
            if validators.is_french_departement(departement):
                departements.append(departement)
            else:
                message = (
                    "Le numéro de département français « %s » n'est pas valide."
                    % request.GET.get(field)
                )
                return JsonResponse({"message": message}, status=400)

    if departements:
        carriers = carriers.filter(
            Q(working_area=models.WORKING_AREA_INTERNATIONAL)
            | Q(working_area=models.WORKING_AREA_FRANCE)
            | Q(
                working_area__in=(
                    models.WORKING_AREA_DEPARTEMENT,
                    models.WORKING_AREA_REGION,
                ),
                working_area_departements__contains=departements,
            )
        )

    # Filtering on specialities
    specialities = request.GET.getlist("specialities[]")
    if specialities:
        carriers = carriers.filter(specialities__contains=specialities)

    # Ordering

    # Raw SQL is more simple here than Case, When, etc
    order_departement_counter = OrderBy(
        RawSQL(
            """
            CASE working_area
            WHEN 'DEPARTEMENT' THEN array_length(working_area_departements, 1)
            WHEN 'REGION' THEN array_length(working_area_departements, 1)
            WHEN 'FRANCE' THEN 101
            WHEN 'INTERNATIONAL' THEN 102
            END
        """,
            (),
        ),
        nulls_last=True,
    )

    order_by_list = [order_departement_counter]

    # By departement of the company if relevant
    if departements:
        order_departement_company = RawSQL(
            "CASE WHEN departement IN (%s) THEN 1 ELSE 2 END", (",".join(departements),)
        )
        order_by_list.append(order_departement_company)

    # By completeness and enseigne
    order_by_list.extend(("-completeness", "enseigne"))
    carriers = carriers.order_by(*order_by_list).values(*CARRIER_LIST_FIELDS)[
        : settings.CARRIERS_LIMIT
    ]

    payload = {"carriers": list(carriers)}
    if len(payload["carriers"]) == settings.CARRIERS_LIMIT:
        payload["limit"] = settings.CARRIERS_LIMIT
    return JsonResponse(payload)


def get_carrier_value_for_json(k, v):
    return str(v) if k == "telephone" else v


def get_carrier_changes(carrier, cleaned_payload):
    old_data_changed = {}
    old_data = {field: getattr(carrier, field) for field in cleaned_payload}
    for k, v in old_data.items():
        if v != cleaned_payload[k]:
            old_data_changed[k] = get_carrier_value_for_json(k, v)

    return old_data_changed


def add_carrier_log(carrier, old_data_changed, cleaned_payload):
    """
    Add an entry to carrier log. Take care to create an initial entry
    with old data when no entries exist yet.
    """
    if not models.CarrierLog.objects.filter(carrier=carrier).exists():
        models.CarrierLog.objects.create(carrier=carrier, data=old_data_changed)

    new_data_changed = {
        k: get_carrier_value_for_json(k, cleaned_payload[k])
        for k in old_data_changed.keys()
    }
    models.CarrierLog.objects.create(carrier=carrier, data=new_data_changed)


RE_MANY_COMMAS = re.compile(r",+")


def carrier_detail(request, carrier_siret):
    response_json = {}
    # Access to deleted carriers is allowed.
    # Get existing carrier if any
    carrier = get_object_or_404(models.Carrier, siret=carrier_siret)

    if request.method == "PATCH":
        if not request.content_type == "application/json":
            return JsonResponse(
                {"message": "Seules les requêtes PATCH en JSON sont prises en charge."},
                status=400,
            )

        payload, response = core_views.request_load(request)
        if response:
            return response

        # Emails stored in DB aren't exposed before validation.
        # If not provided on first validation, emails are deleted (and logged).
        if not carrier.validated_at and not "email" in payload:
            payload["email"] = ""

        # Form is not bound to the carrier instance but we need it to check edit code
        form = forms.DetailForm(payload, carrier=carrier)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors}, status=400)

        # Exclude edit code from changes if not up to you to define it!
        form.cleaned_data.pop("edit_code")

        # Limit cleaned_data to the keys of the payload but only accept keys of cleaned_data (intersection)
        # to only update the submitted values
        cleaned_payload = {
            k: form.cleaned_data[k] for k in payload.keys() if k in form.cleaned_data
        }

        # Only set in PATCH request
        confirmation_email_to_send = False

        # Only apply the submitted values if they are different in DB
        old_data_changed = get_carrier_changes(carrier, cleaned_payload)
        if old_data_changed:
            # Data has been modified so saving is required
            # Don't use form.save to edit only the submitted fields of the instance
            updated_fields = list(old_data_changed.keys())

            for field in updated_fields:
                setattr(carrier, field, cleaned_payload[field])

            if "email" in updated_fields:
                # New email should invalidate email confirmation and edit code
                carrier.email_confirmed_at = None
                carrier.reset_edit_code()
                updated_fields.extend(
                    ["email_confirmed_at", "edit_code", "edit_code_at"]
                )
                # If not empty
                if carrier.email:
                    confirmation_email_to_send = True

            carrier.validated_at = timezone.now()
            updated_fields.append("validated_at")

            with transaction.atomic(savepoint=False):
                carrier.save(force_update=True, update_fields=updated_fields)
                add_carrier_log(carrier, old_data_changed, cleaned_payload)

            mails.mail_managers_changes(carrier, old_data_changed)

        if confirmation_email_to_send:
            mails.mail_carrier_to_confirm_email(carrier)

        response_json["confirmation_email_sent"] = confirmation_email_to_send

    transporteur_detail_fields = CARRIER_DETAIL_FIELDS
    if carrier.validated_at:
        # Only emails of validated carriers are provided
        transporteur_detail_fields += ("email",)

    carrier_json = get_carrier_as_json(carrier, transporteur_detail_fields)
    carrier_json["other_facilities"] = get_other_facilities_as_json(carrier)
    carrier_json["latest_certificate"] = get_latest_certificate_as_json(carrier)
    response_json["carrier"] = carrier_json
    return JsonResponse(response_json)


def carrier_confirm_email(request, carrier_siret, token):
    try:
        carrier = models.Carrier.objects.get(pk=carrier_siret)
    except models.Carrier.DoesNotExist:
        carrier = None

    if carrier and tokens.email_confirmation_token.check_token(carrier, token):
        carrier.lock()
        carrier.save()
        mails.mail_managers_lock(carrier)
        return JsonResponse({"message": "L'adresse électronique est confirmée."})

    return JsonResponse(
        {"message": "Impossible de confirmer l'adresse électronique."}, status=400
    )


def carrier_send_edit_code(request, carrier_siret):
    carrier = get_object_or_404(models.Carrier, siret=carrier_siret)

    if not carrier.is_locked():
        return JsonResponse(
            {"message": "L'adresse électronique n'est pas confirmée."}, status=409
        )

    if carrier.edit_code_has_expired():
        carrier.set_edit_code()
        try:
            mails.mail_carrier_edit_code(carrier)
        except ConnectionRefusedError as e:
            carrier.reset_edit_code()
            sentry_sdk.capture_exception(e)
            message = "Impossible d'envoyer le code de modification."
            status = 503
        else:
            carrier.save()
            message = "Un code de modification a été envoyé par courriel."
            status = 201
    else:
        message = "Le précédent code de modification envoyé est toujours valide."
        status = 200

    return JsonResponse(
        {
            "message": message,
            "email": carrier.email,
            "edit_code_at": carrier.edit_code_at,
            "edit_code_timeout_at": carrier.get_edit_code_timeout_at(),
        },
        status=status,
    )


# FIXME Check POST is done by carrier owner
def _carrier_sign_certificate(request, carrier_siret):
    carrier = get_object_or_404(models.Carrier, siret=carrier_siret)

    serializer, response = core_views.request_validate(
        request, carriers_serializers.CertificateSerializer
    )
    if response:
        return response

    kind = serializer.validated_data.pop("kind")
    models.CarrierCertificate.objects.create(
        carrier=carrier, kind=kind, data=serializer.validated_data
    )
    return JsonResponse(
        {"carrier": get_carrier_as_json(carrier, CARRIER_DETAIL_FIELDS)}
    )


def _carrier_get_certificate(request, carrier_siret, as_pdf=True):
    carrier = get_object_or_404(models.Carrier, siret=carrier_siret)

    # Get latest certificate of any kinds
    certificate = carrier.get_latest_certificate()
    if certificate is None:
        return JsonResponse(
            {"message": "Aucun certificat pour le transporteur %s" % carrier.enseigne},
            status=404,
        )

    template_name = (
        "certificate_workers.html"
        if certificate.kind == models.CERTIFICATE_WORKERS
        else "certificate_no_workers.html"
    )
    qr_code = core_pdf.get_qr_code(
        settings.HTTP_CLIENT_URL + "transporteur/" + carrier.siret
    )
    response = render(
        request,
        template_name,
        {
            "carrier": carrier,
            "certificate": certificate,
            "formated_date": date_format(certificate.created_at),
            "qr_code": qr_code,
        },
    )

    if as_pdf:
        return core_pdf.pdf_response(
            response, "adock-%s-attestation-%s.pdf" % (carrier.siret, certificate.pk)
        )

    return response


def carrier_certificate(request, *args, **kwargs):
    if request.method == "POST":
        return _carrier_sign_certificate(request, *args, **kwargs)

    return _carrier_get_certificate(request, *args, **kwargs)
