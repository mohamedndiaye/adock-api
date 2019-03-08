import re

from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.db.models.expressions import OrderBy, RawSQL
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.formats import date_format

from adock.core import pdf as core_pdf
from adock.core import views as core_views

from . import mails, models, tokens, validators
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
)

CARRIER_DETAIL_FIELDS = (
    "siret",
    "raison_sociale",
    "enseigne",
    "gestionnaire",
    "adresse",
    "code_postal",
    "ville",
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
    "objectif_co2",
    "objectif_co2_begin",
    "objectif_co2_end",
    "deleted_at",
    "sirene_deleted_at",
    "longitude",
    "latitude",
    # is_locked boolean is added to indicate if editable is present
)

# From CarrierEditable
CARRIER_DETAIL_EDITABLE_FIELDS = (
    # "telephone" is manually added
    "email",
    "working_area",
    "working_area_departements",
    "specialities",
    "website",
    "description",
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


def get_carrier_as_json(carrier):
    carrier_json = {}

    for field in CARRIER_DETAIL_FIELDS:
        carrier_json[field] = getattr(carrier, field)

    editable = carrier.editable
    carrier_json["is_locked"] = bool(editable.confirmed_at)
    carrier_json["telephone"] = (
        editable.telephone
        if isinstance(editable.telephone, str)
        else "0" + editable.telephone.format_as(settings.PHONENUMBER_DEFAULT_REGION)
    )

    for field in CARRIER_DETAIL_EDITABLE_FIELDS:
        carrier_json[field] = getattr(editable, field)

    return carrier_json


def get_carriers_as_json(carriers, order_by_list):
    return list(
        carriers.order_by(*order_by_list)
        .values(*CARRIER_LIST_FIELDS)
        .annotate(working_area=F("editable__working_area"))[: settings.CARRIERS_LIMIT]
    )


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
            Q(editable__working_area=models.WORKING_AREA_INTERNATIONAL)
            | Q(editable__working_area=models.WORKING_AREA_FRANCE)
            | Q(
                editable__working_area__in=(
                    models.WORKING_AREA_DEPARTEMENT,
                    models.WORKING_AREA_REGION,
                ),
                editable__working_area_departements__contains=departements,
            )
        )

    # Filtering on specialities
    specialities = request.GET.getlist("specialities[]")
    if specialities:
        carriers = carriers.filter(editable__specialities__contains=specialities)

    # Ordering

    # Raw SQL is more simple here than Case, When, etc
    order_departement_counter = OrderBy(
        RawSQL(
            """
            CASE "carrier_editable"."working_area"
            WHEN 'DEPARTEMENT' THEN array_length("carrier_editable"."working_area_departements", 1)
            WHEN 'REGION' THEN array_length("carrier_editable"."working_area_departements", 1)
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
    payload = {"carriers": get_carriers_as_json(carriers, order_by_list)}

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


RE_MANY_COMMAS = re.compile(r",+")


def carrier_detail(request, carrier_siret):
    # Access to deleted carriers is allowed.
    # Get existing carrier if any
    carrier = get_object_or_404(
        models.Carrier.objects.select_related("editable"), siret=carrier_siret
    )

    if request.method == "POST":
        if request.user.is_anonymous:
            return JsonResponse(
                {
                    "message": "Vous devez être connecté pour modifier une fiche transporteur."
                },
                status=401,
            )

        notification_email_to_send = False
        new_serializer, response = core_views.request_validate(
            request, carriers_serializers.CarrierEditableSerializer
        )
        if response:
            return response

        if carrier.editable:
            # 1. Compare values
            changed_fields = []
            current_serializer = carriers_serializers.CarrierEditableSerializer(
                carrier.editable
            )

            current_data = current_serializer.data
            validated_data = new_serializer.validated_data
            for field in validated_data:
                if current_data[field] != validated_data[field]:
                    changed_fields.append(field)

            new_editable_to_create = bool(changed_fields)

            # 2. Previous email for notification
            if "email" in changed_fields and carrier.editable.email:
                notification_email_to_send = True
        else:
            new_editable_to_create = True

        if new_editable_to_create:
            new_carrier_editable = new_serializer.save(
                carrier=carrier, created_by=request.user
            )

            if notification_email_to_send:
                mails.mail_carrier_to_old_email(
                    carrier, changed_fields, current_data, validated_data
                )
            mails.mail_carrier_editable_to_confirm(
                new_carrier_editable, changed_fields, current_data, validated_data
            )
            mails.mail_managers_carrier_changes(
                carrier, changed_fields, current_data, validated_data
            )

    carrier_json = get_carrier_as_json(carrier)
    carrier_json["other_facilities"] = get_other_facilities_as_json(carrier)
    carrier_json["latest_certificate"] = get_latest_certificate_as_json(carrier)
    return JsonResponse({"carrier": carrier_json})


def carrier_editable_confirm(request, carrier_editable_id, token):
    try:
        carrier_editable = models.CarrierEditable.objects.select_related("carrier").get(
            pk=carrier_editable_id
        )
    except models.CarrierEditable.DoesNotExist:
        carrier_editable = None
        return JsonResponse({"message": "La modification n'existe pas."})

    data = {"siret": carrier_editable.carrier_id}
    if carrier_editable and tokens.carrier_editable_token.check_token(
        carrier_editable, token
    ):
        with transaction.atomic(savepoint=False):
            carrier_editable.confirmed_at = timezone.now()
            carrier_editable.save()
            carrier_editable.carrier.editable = carrier_editable
            carrier_editable.carrier.save()

        mails.mail_managers_carrier_confirmed(carrier_editable.carrier)
        data["message"] = "Les modifications de la fiche sont confirmées."
        return JsonResponse(data)

    data[
        "message"
    ] = "Impossible de confirmer les modifications de la fiche transporteur."
    return JsonResponse(data, status=400)


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
    return JsonResponse({"carrier": get_carrier_as_json(carrier)})


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
