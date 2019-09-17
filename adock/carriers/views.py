import re

from django.conf import settings
from django.db import connection, transaction
from django.db.models import F, Q
from django.db.models.expressions import OrderBy, RawSQL
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.formats import date_format
from django.views.decorators.http import require_POST

from ..core import pdf as core_pdf
from ..core import views as core_views
from ..accounts import mails as accounts_mails
from ..accounts import views as accounts_views

from . import mails as carriers_mails
from . import models as carriers_models
from . import tokens as carriers_tokens
from . import validators as carriers_validators
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
    # get_siren is added too
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
    "sirene_exists",
    "sirene_closed_at",
    "longitude",
    "latitude",
    # is_confirmed boolean is added to indicate if editable is present
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
    "sirene_closed_at",
    "siret",
    "ville",
)


def format_telephone(phonenumber):
    return (
        phonenumber
        if isinstance(phonenumber, str)
        else "0" + phonenumber.format_as(settings.PHONENUMBER_DEFAULT_REGION)
    )


def get_carrier_as_json(user, carrier):
    carrier_json = {}

    for field in CARRIER_DETAIL_FIELDS:
        carrier_json[field] = getattr(carrier, field)
    carrier_json["siren"] = carrier.get_siren()

    editable = carrier.editable
    carrier_json["is_confirmed"] = bool(editable.confirmed_at)
    carrier_json["telephone"] = format_telephone(editable.telephone)

    for field in CARRIER_DETAIL_EDITABLE_FIELDS:
        carrier_json[field] = getattr(editable, field)

    carrier_json["user_is_owner"] = (not user.is_anonymous) and (user.id == editable.created_by_id)

    # License renewal on going, we don't set the field if we don't have the
    # information (paper process for example)
    latest_license_renewal = carrier.get_latest_license_renewal()
    if latest_license_renewal is not None and latest_license_renewal.delivered_at is None:
        carrier_json["license_renewal_on_going"] = latest_license_renewal.confirmed_at.date()

    return carrier_json


def get_carriers_as_json(carriers, order_by_list, limit=None, with_details=False):
    carriers = (
        carriers.order_by(*order_by_list)
        .values(*CARRIER_LIST_FIELDS)
        .annotate(working_area=F("editable__working_area"))
    )
    if limit:
        return list(carriers[:limit])
    else:
        return list(carriers)


def get_other_facilities_as_json(carrier):
    other_facilities = (
        carriers_models.Carrier.objects.filter(
            siret__startswith=carrier.siret[: carriers_validators.SIREN_LENGTH]
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


def carrier_search_q(carriers, q):
    """Filtering on enseigne, SIREN/SIRET, zip code"""
    # Remove ignored characters
    q = q.translate(carriers_validators.SEARCH_Q_TRANS_TABLE).upper()
    if carriers_validators.RE_ONLY_DIGITS_AND_SPACES.match(q):
        # Zip code or SIREN/SIRET number so we remove useless spaces
        q = q.replace(" ", "")
        if len(q) > 5:
            # SIREN/SIRET
            return carriers.filter(siret__startswith=q)

        # Comment #1
        # Zip code are shorter than 5 digits but could be a digit in
        # the company name too (limited to 5). Criteria contains
        # only digits so the filtering will return same results
        # against enseigne and enseigne_unaccent, however it's
        # better to compare against enseigne_unaccent to reduce the
        # number of DB indexes.
        return carriers.filter(
            Q(code_postal__startswith=q) | Q(enseigne_unaccent__contains=q)
        )

    # Spaces are used to split q as a list of criterion
    criterion_list = q.split(" ")
    for criterion in criterion_list:
        criterion = criterion.strip()
        if not criterion:
            continue

        if carriers_validators.RE_ONLY_DIGITS.match(criterion):
            # criterion contains only digits
            if len(criterion) > 5:
                # SIREN is longer than 5
                carriers = carriers.filter(siret__startswith=criterion)
            else:
                # Idem as comment #1
                carriers = carriers.filter(
                    Q(code_postal__startswith=criterion)
                    | Q(enseigne_unaccent__contains=criterion)
                )
        else:
            # Dynamic unaccent is too slow (237x slower!) so we created a dedicated field
            # in DB and use raw SQL too avoid useless replaces added by the ORM.
            # The search criterion contains at least one not digit character so search on name
            carriers = carriers.filter(enseigne_unaccent__ucontains=criterion)

    return carriers


class SearchException(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self)


def carrier_search_get_limit(request):
    limit = request.GET.get("limit")
    if limit:
        try:
            limit = int(limit)
        except ValueError:
            raise SearchException(
                message="La limite du nombre de résultats « %s » n'est pas un nombre valide."
                % limit
            )

        if limit <= 0:
            raise SearchException(
                message="La limite ne peut pas être un nombre négatif « %d »." % limit
            )

        limit = min(limit, settings.CARRIERS_LIMIT)
    else:
        limit = settings.CARRIERS_LIMIT

    return limit


def carrier_search(request):
    """The search allows to filter on:
       - partial enseigne or SIRET
       - type of the license (LC heavy or LTI light)
    """
    carriers = carriers_models.Carrier.objects.filter(
        deleted_at=None, sirene_closed_at=None
    )
    q = request.GET.get("q")
    if q:
        carriers = carrier_search_q(carriers, q)

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
            if carriers_validators.is_french_departement(departement):
                departements.append(departement)
            else:
                message = (
                    "Le numéro de département français « %s » n'est pas valide."
                    % request.GET.get(field)
                )
                return JsonResponse({"message": message}, status=400)

    if departements:
        carriers = carriers.filter(
            Q(editable__working_area=carriers_models.WORKING_AREA_INTERNATIONAL)
            | Q(editable__working_area=carriers_models.WORKING_AREA_FRANCE)
            | Q(
                editable__working_area__in=(
                    carriers_models.WORKING_AREA_DEPARTEMENT,
                    carriers_models.WORKING_AREA_REGION,
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

    try:
        limit = carrier_search_get_limit(request)
    except SearchException as e:
        return JsonResponse({"message": e.message}, status=e.status_code)
    payload = {"carriers": get_carriers_as_json(carriers, order_by_list, limit)}

    if len(payload["carriers"]) == limit:
        payload["limit"] = limit

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


def check_user_is_not_anonymous(user):
    if not user or user.is_anonymous:
        return JsonResponse(
            {
                "message": "Vous devez être connecté pour modifier une fiche entreprise."
            },
            status=401,
        )


def check_user_has_accepted_cgu(user):
    if not user or not user.has_accepted_cgu:
        return JsonResponse(
            {"message": "Vous devez accepter les Conditions Générales d'Utilisation."},
            status=401,
        )


def carrier_detail_apply_changes(
    user, carrier, editable_serialized, created_by_email_serialized
):
    """
    Returns a dict with the following fields:
    - confirmation_sent_to: email or None if no changes
    - account_confirmation_sent_to: email of user who create the changes if account not enabled yet
    - old_account_sent_to: email of previous user who edit the carrier if any

    This function is a bit complex for two reasons:
    - to reduce the number of mails sent in subscription, only one mail is sent to
      user account to confirm account creation and carrier changes on same email address
    - a link carrier_user is created on POST to that ressource...
    """
    should_notify_old_email = False
    old_email_notified = False

    validated_data = editable_serialized.validated_data

    # Detect DB inconsistency
    assert carrier.editable

    # Do we need to create a new editable? Only if changes are detected.
    # 1. Compare values
    changed_fields = []
    for field in validated_data:
        if getattr(carrier.editable, field) != validated_data[field]:
            changed_fields.append(field)

    new_editable_to_create = bool(changed_fields)
    # 2. Previous email for notification
    if "email" in changed_fields and carrier.editable.email:
        should_notify_old_email = True

    # Not done on account creation so we should do that now
    should_mail_user = bool(created_by_email_serialized)

    if new_editable_to_create:
        # Changes detected
        new_carrier_editable = editable_serialized.save(
            carrier=carrier, created_by=user
        )

        if should_notify_old_email:
            carriers_mails.mail_carrier_to_old_email(
                changed_fields, carrier.editable, new_carrier_editable
            )
            # Done
            old_email_notified = True

        if should_mail_user and new_carrier_editable.email == user.email:
            # Send a common mail for user account and carrier changes
            accounts_mails.mail_user_to_activate_with_carrier_editable(
                user, changed_fields, carrier.editable, new_carrier_editable
            )
            should_mail_user = False
        else:
            # Send only an email for carrier changes
            carriers_mails.mail_carrier_editable_to_confirm(
                changed_fields, carrier.editable, new_carrier_editable
            )

        carriers_mails.mail_managers_carrier_changes(
            changed_fields, carrier.editable, new_carrier_editable
        )

    # Changes or not, a relation should be created between the carrier and the user
    # but only if this relation doesn't exist yet. Raw SQL for upsert.
    with connection.cursor() as cursor:
        cursor.execute("""
            insert into carrier_user (carrier_id, user_id, created_at) values (%s, %s, now())
            on conflict do nothing returning id""",
            [carrier.pk, user.pk]
        )
        carrier_user_is_created = cursor.fetchone()

    if not old_email_notified and carrier_user_is_created:
        # Only if the old email address hasn't been notified yet
        carriers_mails.mail_carrier_to_old_email_for_new_user(carrier.editable, user)
        old_email_notified = True

    if should_mail_user:
        accounts_mails.mail_user_to_activate(user)

    confirmation_sent_to = (
        new_carrier_editable.email if new_editable_to_create else None
    )
    account_confirmation_sent_to = user.email if should_mail_user else None
    notification_sent_to = carrier.editable.email if old_email_notified else None
    return {
        "confirmation_sent_to": confirmation_sent_to,
        "account_confirmation_sent_to": account_confirmation_sent_to,
        "notification_sent_to": notification_sent_to
    }


def carrier_detail(request, carrier_siret):
    # Response will include a carrier attribute
    data_json = {}
    # Access to deleted carriers is allowed.
    carrier = get_object_or_404(
        carriers_models.Carrier.objects.select_related("editable"), siret=carrier_siret
    )

    if request.method == "POST":
        editable_serialized, response = core_views.request_validate(
            request, carriers_serializers.CarrierEditableSerializer
        )
        if response:
            return response

        # If not anonymous, the request user is used.
        user = request.user
        created_by_email_serialized = None
        if user.is_anonymous:
            # Else it's allowed to used a not yet enabled user which
            # the created_by_email is provided in request.
            # The current subscribe process of UI uses that.
            payload, response = core_views.request_load(request)
            if response:
                return response

            if "created_by_email" in payload:
                # Only not enabled users are accepted
                created_by_email_serialized, response = core_views.request_validate(
                    request, carriers_serializers.CreatedByEmailSerializer
                )
                if response:
                    return response
                user = created_by_email_serialized.created_by

        response = check_user_is_not_anonymous(user)
        if response:
            return response

        response = check_user_has_accepted_cgu(user)
        if response:
            return response

        mails_sent_to = carrier_detail_apply_changes(
            user, carrier, editable_serialized, created_by_email_serialized
        )
        # Add them to the response
        data_json.update(mails_sent_to)
        data_json["message"] = (
            "Vous devez confirmer les changements de la fiche entreprise "
            "en cliquant sur le lien envoyé à « %s »."
        ) % mails_sent_to["confirmation_sent_to"]

        if mails_sent_to["account_confirmation_sent_to"]:
            data_json["account_message"] = (
                accounts_views.ACCOUNT_CREATED_MESSAGE
                % mails_sent_to["account_confirmation_sent_to"]
            )

    carrier_json = get_carrier_as_json(request.user, carrier)
    carrier_json["other_facilities"] = get_other_facilities_as_json(carrier)
    carrier_json["latest_certificate"] = get_latest_certificate_as_json(carrier)
    data_json["carrier"] = carrier_json
    return JsonResponse(data_json)


def carrier_editable_save(carrier_editable):
    with transaction.atomic(savepoint=False):
        carrier_editable.confirmed_at = timezone.now()
        carrier_editable.save()
        carrier_editable.carrier.editable = carrier_editable
        carrier_editable.carrier.save()


def carrier_editable_confirm(request, carrier_editable_id, token):
    if settings.ENVIRONMENT == "E2E":
        carrier_editable = (
            carriers_models.CarrierEditable.objects.select_related("carrier")
            .filter(carrier__pk="80005226884728")
            .latest()
        )
    else:
        # Production
        carrier_editable = get_object_or_404(
            carriers_models.CarrierEditable.objects.select_related("carrier"),
            pk=carrier_editable_id,
        )

        error_message = (
            "Impossible de confirmer les modifications de la fiche entreprise."
        )
        if (
            carrier_editable.created_by is None
            or not carrier_editable.created_by.is_active
        ):
            return JsonResponse(
                {
                    "siret": carrier_editable.carrier_id,
                    "message": error_message,
                    "submessage": "L'utilisateur ayant effectué les changements n'a pas encore activé son compte.",
                },
                status=400,
            )

        if not carriers_tokens.carrier_editable_token_generator.check_token(
            carrier_editable, token
        ):
            return JsonResponse(
                {
                    "siret": carrier_editable.carrier_id,
                    "message": error_message,
                    "submessage": "Le jeton a peut être expiré ou a déjà été utilisé.",
                },
                status=400,
            )

    carrier_editable_save(carrier_editable)
    carriers_mails.mail_managers_carrier_confirmed(carrier_editable)
    data = {
        "siret": carrier_editable.carrier_id,
        "message": "Les modifications de la fiche entreprise « %s » sont confirmées."
        % (carrier_editable.carrier.enseigne),
    }
    return JsonResponse(data)


def _certificate_sign(request, carrier):
    serializer, response = core_views.request_validate(
        request, carriers_serializers.CertificateSerializer
    )
    if response:
        return response

    # Email is required so another check could be confirmed_at
    if not carrier.editable.email:
        return JsonResponse(
            {
                "message": "Vous devez d'abord confirmer la fiche entreprise avant de générer l'attestation."
            },
            status=400,
        )

    kind = serializer.validated_data.pop("kind")
    certificate = carriers_models.CarrierCertificate.objects.create(
        carrier=carrier,
        created_by=request.user,
        data=serializer.validated_data,
        kind=kind,
    )
    carriers_mails.mail_carrier_certificate_to_confirm(carrier, certificate)
    carriers_mails.mail_managers_new_certificate(certificate)
    return JsonResponse(
        {
            "siret": carrier.siret,
            "message": (
                "Votre attestation a bien été générée ! "
                "Pour l'activer, vous devez la confirmer grâce au lieu envoyé à l’adresse e-mail "
                "de votre entreprise « %s »."
            )
            % carrier.editable.email,
        }
    )


def _certificate_get(request, carrier, as_pdf=True):
    # Get latest certificate of any kinds
    certificate = carrier.get_latest_certificate()
    if certificate is None:
        return JsonResponse(
            {"message": "Aucun certificat pour le transporteur %s" % carrier.enseigne},
            status=404,
        )

    template_name = (
        "certificate_workers.html"
        if certificate.kind == carriers_models.CERTIFICATE_WORKERS
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
            "HOSTNAME": settings.HOSTNAME,
            "HTTP_CLIENT_URL": settings.HTTP_CLIENT_URL,
            "qr_code": qr_code,
        },
    )

    if as_pdf:
        return core_pdf.pdf_response(
            response.content.decode("utf-8"),
            "adock-%s-attestation-%s.pdf" % (carrier.siret, certificate.pk),
        )

    return response


def certificate_detail(request, carrier_siret, as_pdf=True):
    carrier = get_object_or_404(carriers_models.Carrier, siret=carrier_siret)

    if request.method == "POST":
        response = check_user_is_not_anonymous(
            request.user
        ) or check_user_has_accepted_cgu(request.user)
        if response:
            return response

        return _certificate_sign(request, carrier)

    return _certificate_get(request, carrier, as_pdf)


def certificate_confirm(request, certificate_id, token):
    if settings.ENVIRONMENT == "E2E":
        certificate = (
            carriers_models.CarrierCertificate.objects.select_related("carrier")
            .filter(carrier__siret="80005226884728")
            .latest("pk")
        )
    else:
        certificate = get_object_or_404(
            carriers_models.CarrierCertificate.objects.select_related("carrier"),
            pk=certificate_id,
        )
        if not carriers_tokens.certificate_token_generator.check_token(
            certificate, token
        ):
            return JsonResponse(
                {
                    "siret": certificate.carrier_id,
                    "message": "Impossible de confirmer l'attestation.",
                },
                status=400,
            )

    certificate.confirmed_at = timezone.now()
    certificate.save()
    carriers_mails.mail_managers_certificate_confirmed(certificate)
    return JsonResponse(
        {
            "siret": certificate.carrier_id,
            "message": (
                "Votre attestation est confirmée ! "
                "Vous pouvez désormais la consulter sur la fiche de votre entreprise « %s »."
            )
            % certificate.carrier.enseigne,
        }
    )


@require_POST
def license_renewal_ask(request, carrier_siret):
    carrier = get_object_or_404(carriers_models.Carrier, siret=carrier_siret)

    # Only experimental in Bretagne (will be replaced by nice dict with
    # departement number and email when extended)
    if carrier.departement not in ["22", "29", "35", "56"]:
        return JsonResponse(
            {
                "message": (
                    "Cette fonctionnalité est en cours d’expérimentation. "
                    "Son accès est actuellement limité aux établissements dépendants de la DREAL Bretagne."
                    "Vous êtes intéressé par cette fonctionnalité ? Contactez %s ou votre DREAL."
                )
                % settings.SERVER_EMAIL
            },
            status=403,
        )

    # Only possible if the email is set
    if not carrier.editable.email:
        return JsonResponse(
            {
                "message": "La fiche entreprise ne contient pas d'adresse e-mail."
            },
            status=401,
        )

    response = check_user_is_not_anonymous(request.user) or check_user_has_accepted_cgu(
        request.user
    )
    if response:
        return response

    serializer, response = core_views.request_validate(
        request, carriers_serializers.LicenseRenewalSerializer
    )
    if response:
        return response

    license_renewal = carriers_models.CarrierLicenseRenewal.objects.create(
        carrier=carrier,
        created_by=request.user,
        lti_nombre=serializer.validated_data["lti_nombre"],
        lc_nombre=serializer.validated_data["lc_nombre"],
    )
    carriers_mails.mail_carrier_license_renewal_to_confirm(carrier, license_renewal)
    carriers_mails.mail_managers_new_license_renewal(license_renewal)
    return JsonResponse(
        {
            "siret": carrier_siret,
            "message": (
                "Votre demande de renouvellement de licence est enregistrée ! "
                "Pour la transmettre aux services de la DREAL, confirmez cette demande "
                "grâce au lien envoyé à l’adresse e-mail votre entreprise « %s »."
            )
            % carrier.editable.email,
        }
    )


def license_renewal_confirm(request, license_renewal_id, token):
    # Service available in DREAL Bretagne only
    license_renewal = get_object_or_404(
        carriers_models.CarrierLicenseRenewal.objects.select_related("carrier"),
        pk=license_renewal_id,
    )
    if not carriers_tokens.license_renewal_token_generator.check_token(
        license_renewal, token
    ):
        return JsonResponse(
            {
                "siret": license_renewal.carrier_id,
                "message": "Impossible de confirmer la demande de renouvellement de license.",
                "submessage": "Le jeton a peut être expiré ou a déjà été utilisé.",
            },
            status=400,
        )
    license_renewal.confirmed_at = timezone.now()
    license_renewal.save()

    carriers_mails.mail_dreal_license_renewal_with_fallback(license_renewal)
    carriers_mails.mail_managers_license_renewal_confirmed(license_renewal)
    return JsonResponse(
        {
            "siret": license_renewal.carrier_id,
            "message": (
                "Votre demande de renouvellement de license pour l'entreprise de "
                "transport %s est confirmée ! "
                "Elle a été transmise et sera traitée par les services compétents de la DREAL Bretagne."
            )
            % license_renewal.carrier.siret,
        }
    )
