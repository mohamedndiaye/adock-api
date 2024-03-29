import datetime
import json
from urllib.parse import unquote

from django.conf import settings
from django.core import signing
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.utils import crypto, timezone
from django.utils.http import urlencode
from django.views.decorators.http import require_POST
import requests
import sentry_sdk
from jwt_auth import views as jwt_auth_views

from ..carriers import models as carriers_models
from ..carriers import tokens as carriers_tokens
from ..carriers import views as carriers_views
from ..core import views as core_views

from . import mails as accounts_mails
from . import models as accounts_models
from . import serializers as accounts_serializers
from . import tokens as accounts_tokens


ACCOUNT_CREATED_MESSAGE = (
    "Le compte utilisateur A Dock a été créé. "
    "Pour l'activer, cliquez sur le lien envoyé à votre adresse « %s »."
)


@require_POST
def account_create(request):
    """Create an A Dock user account (email as username)"""
    serializer, response = core_views.request_validate(
        request, accounts_serializers.CreateAccountSerializer
    )
    if response:
        return response

    user = accounts_models.User.objects.create_user(
        username=serializer.validated_data["email"],
        email=serializer.validated_data["email"],
        password=serializer.validated_data["password"],
        first_name=serializer.validated_data["first_name"],
        last_name=serializer.validated_data["last_name"],
        has_accepted_cgu=serializer.validated_data["has_accepted_cgu"],
        is_active=False,
    )

    send_activation_link = serializer.validated_data["send_activation_link"]
    accounts_mails.mail_managers_new_account(user, send_activation_link)
    if send_activation_link:
        accounts_mails.mail_user_to_activate(user)
        return JsonResponse({"message": ACCOUNT_CREATED_MESSAGE % user.email})

    # Activation link not sent yet
    return JsonResponse({"message": "Le compte utilisateur A Dock a été créé."})


def account_activate(
    request, user_id, user_token, carrier_editable_id=None, carrier_editable_token=None
):
    if settings.ENVIRONMENT == "E2E":
        # Used only by E2E tests to confirm account
        user = accounts_models.User.objects.get(email="joemartin@example.com")
    else:
        try:
            user = accounts_models.User.objects.get(pk=user_id)
        except accounts_models.User.DoesNotExist:
            return JsonResponse({"message": "L'utilisateur n'existe pas."}, status=400)

        if user.is_active:
            return JsonResponse({"message": "Le compte utilisateur est déjà actif."})

        if not accounts_tokens.account_token_generator.check_token(user, user_token):
            return JsonResponse(
                {
                    "message": "Impossible d'activer le compte utilisateur",
                    "submessage": "Le jeton a peut être expiré ou a déjà été utilisé.",
                },
                status=400,
            )

    user.is_active = True
    user.save()

    message = "{first_name} {last_name}, votre compte utilisateur A Dock est à présent actif !".format(
        first_name=user.first_name, last_name=user.last_name
    )

    # Confirm linked carrier editable if provided
    # FIXME(2019-09-02) This code isn't clean but we aren't sure it will last.
    # Else the UI could do two distinct requests to avoid duplicate.
    if carrier_editable_id and carrier_editable_token:
        try:
            carrier_editable = carriers_models.CarrierEditable.objects.select_related(
                "carrier"
            ).get(pk=carrier_editable_id)
        except carriers_models.CarrierEditable.DoesNotExist:
            carrier_editable = None

        if not carriers_tokens.carrier_editable_token_generator.check_token(
            carrier_editable, carrier_editable_token
        ):
            carrier_editable = None

        if not carrier_editable:
            # Unable to confirm the carrier changes
            message += (
                " . Impossible d'appliquer les changements de la fiche entreprise."
            )
        else:
            carriers_views.carrier_editable_save(carrier_editable)
            message += (
                " Les changements de la fiche entreprise ont été appliqué avec succès."
            )

    json_web_token = jwt_auth_views.jwt_encode_token(user)
    json_data = jwt_auth_views.jwt_get_json_with_token(json_web_token)
    json_data["message"] = message
    return JsonResponse(json_data)


@require_POST
def account_recover_password(request):
    payload, response = core_views.request_load(request)
    if response:
        return response

    if not payload.get("email"):
        return JsonResponse(
            {"message": "La requête ne contient pas le paramètre « email »."},
            status=400,
        )

    # Filter on A_DOCK accounts
    try:
        user = accounts_models.User.objects.get(
            email=payload["email"],
            provider=accounts_models.PROVIDER_A_DOCK,
            is_active=True,
        )
    except accounts_models.User.DoesNotExist:
        return JsonResponse(
            {"message": "L'adresse e-mail est introuvable."}, status=400
        )

    token = accounts_tokens.account_token_generator.make_token(user)
    accounts_mails.mail_user_to_recover_password(user, token)
    return JsonResponse(
        {
            "message": "Un courriel de récupération de mot de passe vous a été envoyé à « %s »."
            % user.email
        }
    )


@require_POST
def account_reset_password(request):
    serializer, response = core_views.request_validate(
        request, accounts_serializers.ResetPasswordSerializer
    )
    if response:
        return response

    user = serializer.validated_data["user"]
    user.set_password(serializer.validated_data["password"])
    user.save()

    return JsonResponse({"message": "Le mot de passe a été modifié avec succès."})


def get_user_confirmations_as_json(user):
    confirmations = []

    # Editable
    editables = user.carrier_changes.select_related("carrier").filter(
        confirmed_at__isnull=True
    )
    for editable in editables:
        confirmations.append(
            {
                "type": "CARRIER_EDITABLE",
                "id": editable.id,
                "title": "Modification de fiche",
                "created_at": editable.created_at,
                "carrier_siret": editable.carrier_id,
                "carrier_enseigne": editable.carrier.enseigne,
                "description": editable.get_description_of_changes(),
            }
        )

    # Certificates
    certificates = user.carrier_certificates.select_related("carrier").filter(
        confirmed_at__isnull=True
    )
    for certificate in certificates:
        confirmations.append(
            {
                "type": "CARRIER_CERTIFICATE",
                "id": certificate.id,
                "title": certificate.get_kind_display(),
                "created_at": certificate.created_at,
                "carrier_siret": certificate.carrier_id,
                "carrier_enseigne": certificate.carrier.enseigne,
                "description": "",
            }
        )

    # License renewals
    license_renewals = user.carrier_license_renewals.select_related("carrier").filter(
        confirmed_at__isnull=True
    )
    for license_renewal in license_renewals:
        confirmations.append(
            {
                "type": "CARRIER_LICENSE_RENEWAL",
                "id": license_renewal.id,
                "title": "Renouvellement de licence",
                "created_at": license_renewal.created_at,
                "carrier_siret": license_renewal.carrier_id,
                "carrier_enseigne": license_renewal.carrier.enseigne,
                "description": license_renewal.get_description(),
            }
        )

    return confirmations


def account_profile(request, extended=False):
    user = request.user
    if user.is_anonymous or not user.is_active:
        return JsonResponse(
            {"message": "Impossible d'obtenir les informations de l'utilisateur."},
            status=401,
        )

    if request.method == "PATCH":
        serializer, response = core_views.request_validate(
            request, accounts_serializers.EditUserSerializer, instance=user
        )
        if response:
            return response

        user = serializer.save()

    user_json = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "last_login": user.last_login,
        "date_joined": user.date_joined.isoformat(),
        "provider": user.provider,
        "provider_display": user.get_provider_display(),
        "provider_data": user.provider_data,
        "is_staff": user.is_staff,
        "has_accepted_cgu": user.has_accepted_cgu,
        "has_subscribed_newsletter": user.has_subscribed_newsletter,
    }

    if extended:
        user_json["carriers"] = carriers_views.get_carriers_as_json(
            user.carriers.all(), ["enseigne"]
        )
        user_json["confirmations"] = get_user_confirmations_as_json(user)

    # Returns only informations not in JWT payload
    return JsonResponse({"user": user_json})


def get_callback_redirect_uri(request):
    redirect_uri = settings.FRANCE_CONNECT_URL_CALLBACK
    next_url = request.GET.get("next")
    if next_url:
        redirect_uri += "?next=%s" % next_url

    return redirect_uri


def france_connect_authorize(request):
    # Possible to set acr_values=eidas1 (eidas2 or eidas3) to filter on provider
    # of identities on a security level.
    if not request.GET.get("nonce"):
        return JsonResponse(
            {"message": "The 'nonce' parameter is not provided."}, status=400
        )

    redirect_uri = get_callback_redirect_uri(request)

    signer = signing.Signer()
    csrf_string = crypto.get_random_string(length=12)
    csrf_signed = signer.sign(csrf_string)
    accounts_models.FranceConnectState.objects.create(csrf_string=csrf_string)

    data = {
        "client_id": settings.FRANCE_CONNECT_CLIENT_ID,
        "nonce": request.GET["nonce"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid gender given_name family_name email address phone",
        "state": csrf_signed,
    }
    return HttpResponseRedirect(
        settings.FRANCE_CONNECT_URLS["authorize"] + "?" + urlencode(data)
    )


def create_or_update_user(user_infos):
    if "address" in user_infos and "formatted" in user_infos["address"]:
        user_infos["address"] = user_infos["address"]["formatted"]

    user, created = accounts_models.User.objects.get_or_create(
        username=user_infos["sub"],
        defaults={
            "email": user_infos["email"],
            "first_name": user_infos.get("given_name", ""),
            "last_name": user_infos.get("family_name", ""),
            "provider": accounts_models.PROVIDER_FRANCE_CONNECT,
            "provider_data": user_infos,
        },
    )

    if not created:
        # Forced update (may be it will possible to set a different email later)
        user.email = user_infos.get("email", "")
        user.first_name = user_infos.get("given_name", "")
        user.family_name = user_infos.get("family_name", "")
        user.provider = accounts_models.PROVIDER_FRANCE_CONNECT
        user.provider_data = user_infos
        try:
            user.save()
        except IntegrityError as e:
            # Don't update the fields
            sentry_sdk.capture_exception(e)
            # Take care to refresh the user...

    return user, created


def state_is_valid(state):
    if not state:
        return False

    signer = signing.Signer()
    try:
        csrf_string = signer.unsign(unquote(state))
    except signing.BadSignature:
        return False

    try:
        accounts_models.FranceConnectState.objects.get(csrf_string=csrf_string)
    except accounts_models.FranceConnectState.DoesNotExist as e:
        sentry_sdk.capture_exception(e)
        return False
    except accounts_models.FranceConnectState.MultipleObjectsReturned:
        sentry_sdk.capture_exception(e)
        return False

    accounts_models.FranceConnectState.objects.filter(
        Q(created_at__lte=timezone.now() - datetime.timedelta(hours=1))
        | Q(csrf_string=csrf_string)
    ).delete()
    return True


def france_connect_callback(request):
    # state is also available and should be checked (#1)
    code = request.GET.get("code")
    if code is None:
        return JsonResponse(
            {"message": "La requête ne contient pas le paramètre « code »."}, status=400
        )

    state = request.GET.get("state")
    if not state_is_valid(state):
        return JsonResponse(
            {"message": "Le paramètre « state » n'est pas valide."}, status=400
        )

    redirect_uri = get_callback_redirect_uri(request)

    data = {
        "client_id": settings.FRANCE_CONNECT_CLIENT_ID,
        "client_secret": settings.FRANCE_CONNECT_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    # Exceptions catched by Sentry
    response = requests.post(
        settings.FRANCE_CONNECT_URLS["token"], data=data, timeout=60
    )

    if response.status_code != 200:
        message = "Impossible d'obtenir le jeton de FranceConnect."
        sentry_sdk.capture_message("%s\n%s" % (message, response.content))
        # The response is certainly ignored by FC but it's convenient for our tests
        return JsonResponse({"message": message}, status=response.status_code)

    # Contains access_token, token_type, expires_in, id_token
    token_data = response.json()
    # A token has been provided so it's time to fetch associated user infos
    # because the token is only valid for 5 seconds.
    response = requests.get(
        settings.FRANCE_CONNECT_URLS["userinfo"],
        params={"schema": "openid"},
        headers={"Authorization": "Bearer " + token_data["access_token"]},
        timeout=60,
    )
    if response.status_code != 200:
        message = "Impossible d'obtenir les informations utilisateur de FranceConnect."
        sentry_sdk.capture_message(message)
        return JsonResponse({"message": message}, status=response.status_code)

    try:
        user_infos = json.loads(response.content.decode("utf-8"))
    except json.decoder.JSONDecodeError:
        return JsonResponse(
            {"message": "Impossible de décoder les informations utilisateur."},
            status=400,
        )

    if "sub" not in user_infos:
        return JsonResponse(
            {"message": "Le paramètre « sub » n'a pas été retourné par FranceConnect."},
            status=400,
        )

    user, created = create_or_update_user(user_infos)
    if created:
        accounts_mails.mail_managers_new_account(user)

    # Return JWT with id_token to allow logout from FC
    if user is None:
        return JsonResponse({"message": "Aucun utilisateur."})

    return JsonResponse(
        {
            "token_type": token_data.get("token_type", ""),
            "token": jwt_auth_views.jwt_encode_token(user),
            "expires_in": settings.JWT_EXPIRATION_DELTA.total_seconds(),
            "id_token": token_data.get("id_token", ""),
        }
    )


def france_connect_logout(request):
    if request.user.is_anonymous:
        return JsonResponse({"message": "L'utilisateur n'est pas authentifié."})

    id_token = request.GET.get("id_token")
    if not id_token:
        return JsonResponse(
            {"message": "Le paramètre « id_token » est manquant."}, status=400
        )

    params = {
        "id_token_hint": id_token,
        "state": "adock",
        "post_logout_redirect_uri": settings.FRANCE_CONNECT_URL_POST_LOGOUT,
    }
    redirect_url = settings.FRANCE_CONNECT_URLS["logout"] + "/?" + urlencode(params)
    return JsonResponse({"url": redirect_url}, status=302)
