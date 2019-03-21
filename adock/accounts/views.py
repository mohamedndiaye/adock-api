import datetime
import json
import logging
from urllib.parse import unquote

from django.conf import settings
from django.core import signing
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.utils import crypto, timezone
from django.views.decorators.http import require_POST
from django.utils.http import urlencode
import requests
import sentry_sdk
from jwt_auth import views as jwt_auth_views

from adock.core import views as core_views
from adock.carriers import models as carriers_models
from adock.carriers import views as carriers_views

from . import mails as accounts_mails
from . import models as accounts_models
from . import serializers as accounts_serializers
from . import tokens as accounts_tokens

logger = logging.getLogger(__name__)


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
        is_active=False,
    )
    token = accounts_tokens.account_activation_token.make_token(user)
    accounts_mails.mail_user_to_activate(user, token)
    accounts_mails.mail_managers_new_account(user)
    return JsonResponse(
        {"message": "Un email vous a été envoyé à « %s »." % user.email}
    )


def account_activate(request, user_id, token):
    try:
        user = accounts_models.User.objects.get(pk=user_id)
    except accounts_models.User.DoesNotExist:
        return JsonResponse({"message": "L'utilisateur n'existe pas."}, status=400)

    if user.is_active:
        return JsonResponse({"message": "Le compte utilisateur est déjà actif."})

    if not accounts_tokens.account_activation_token.check_token(user, token):
        return JsonResponse(
            {"message": "Le jeton d'activation n'est pas valide."}, status=400
        )

    user.is_active = True
    user.save()

    token = jwt_auth_views.jwt_encode_token(user)
    json_data = jwt_auth_views.jwt_get_json_with_token(token)
    json_data["message"] = "Le compte utilisateur est activé."
    return JsonResponse(json_data)


def account_profile(request, extended=False):
    if request.user.is_anonymous or not request.user.is_active:
        return JsonResponse(
            {"message": "Impossible d'obtenir les informations de l'utilisateur."},
            status=401,
        )

    if request.method == "PATCH":
        serializer, response = core_views.request_validate(
            request, accounts_serializers.EditUserSerializer, instance=request.user
        )
        if response:
            return response

        request.user = serializer.save()

    user = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email,
        "last_login": request.user.last_login,
        "date_joined": request.user.date_joined,
        "provider": request.user.provider,
        "provider_display": request.user.get_provider_display(),
        "has_accepted_cgu": request.user.has_accepted_cgu,
    }

    if extended:
        carriers = (
            carriers_models.Carrier.objects.filter(changes__created_by=request.user)
            .select_related("editable")
            .distinct()
        )
        user["carriers"] = carriers_views.get_carriers_as_json(carriers, ["enseigne"])

    # Returns only informations not in JWT payload
    return JsonResponse({"user": user})


def france_connect_authorize(request):
    # Possible to set acr_values=eidas1 (eidas2 or eidas3) to filter on provider
    # of identities on a security level.
    if not request.GET.get("nonce"):
        return JsonResponse(
            {"message": "The 'nonce' parameter is not provided."}, status=400
        )

    signer = signing.Signer()
    csrf_string = crypto.get_random_string(length=12)
    csrf_signed = signer.sign(csrf_string)
    accounts_models.FranceConnectState.objects.create(csrf_string=csrf_string)

    data = {
        "client_id": settings.FRANCE_CONNECT_CLIENT_ID,
        "nonce": request.GET["nonce"],
        "redirect_uri": settings.FRANCE_CONNECT_URL_CALLBACK,
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
            logger.error("Unable to update the user: %s", e.__cause__)
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

    data = {
        "client_id": settings.FRANCE_CONNECT_CLIENT_ID,
        "client_secret": settings.FRANCE_CONNECT_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.FRANCE_CONNECT_URL_CALLBACK,
    }
    response = requests.post(settings.FRANCE_CONNECT_URLS["token"], data=data)
    if response.status_code != 200:
        message = "Impossible d'obtenir le jeton de FranceConnect."
        logger.error(message)
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
    )
    if response.status_code != 200:
        message = "Impossible d'obtenir les informations utilisateur de FranceConnect."
        logger.error(message)
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
    if id_token:
        data = {
            "id_token_hint": id_token,
            "state": "test",
            "post_logout_redirect_uri": settings.HTTP_CLIENT_URL,
        }
        response = requests.get(settings.FRANCE_CONNECT_URLS["logout"], params=data)
        if response.status_code != 200:
            message = "Impossible de déconnecter l'utilisateur de FranceConnect."
            logger.error(message)
            sentry_sdk.capture_message(message)
            return JsonResponse({"message": message}, status=400)

    return JsonResponse({"message": "L'utilisateur est déconnecté."})
