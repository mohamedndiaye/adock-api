import json
import logging
import requests

from django.conf import settings
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST

# from django.utils.crypto import get_random_string
from django.utils.http import urlencode
import sentry_sdk
from jwt_auth import forms as jwt_auth_forms

from adock.core import views as core_views

from . import models as accounts_models
from . import serializers as accounts_serializers

logger = logging.getLogger(__name__)


@require_POST
def account_create(request):
    """Create a local user account"""
    serializer, response = core_views.request_validate(
        request, accounts_serializers.AccountSerializer
    )
    if response:
        return response

    user = accounts_models.User.objects.create_user(
        email=serializer.validated_data["email"],
        password=serializer.validated_data["password"],
        first_name=serializer.validated_data["first_name"],
        last_name=serializer.validated_data["last_name"],
        is_active=False,
    )

    return JsonResponse(
        {"message": "Compte utilisateur créé pour %s" % user.get_full_name()}
    )
    # FIXME mail to validate


def france_connect_authorize(request):
    # Possible to set acr_values=eidas1 (eidas2 or eidas3) to filter on provider
    # of identities on a security level.
    data = {
        "client_id": settings.FRANCE_CONNECT_CLIENT_ID,
        # FIXME nonce should be tied to the user request (CSRF?) and checked in provided id token (cf #2)
        "nonce": "test",
        "redirect_uri": settings.FRANCE_CONNECT_URL_CALLBACK,
        "response_type": "code",
        "scope": "openid identite_pivot email address phone",
        # FIXME state should be random or CSRF? and checked (cf #1)
        "state": "test",
    }
    return HttpResponseRedirect(
        settings.FRANCE_CONNECT_URLS["authorize"] + "?" + urlencode(data)
    )


def create_or_update_user(user_infos):
    if "address" in user_infos and "formatted" in user_infos["address"]:
        user_infos["address"] = user_infos["address"]["formatted"]

    try:
        user, created = accounts_models.User.objects.get_or_create(
            provider=accounts_models.PROVIDER_FRANCE_CONNECT,
            provider_data__sub=user_infos["sub"],
            defaults={
                "email": user_infos["email"],
                "first_name": user_infos.get("given_name", ""),
                "last_name": user_infos.get("family_name", ""),
                "provider": accounts_models.PROVIDER_FRANCE_CONNECT,
                "provider_data": user_infos,
            },
        )
    except IntegrityError as e:
        logger.error("Unable to create the user: %s", e.__cause__)
        sentry_sdk.capture_exception(e)
        return None, False

    if not created:
        # Forced update (may be it will possible to set a different email later)
        user.email = user_infos.get("email", "")
        user.first_name = user_infos.get("given_name", "")
        user.family_name = user_infos.get("family_name", "")
        user.provider_data = user_infos
        try:
            user.save()
        except IntegrityError as e:
            # Don't update the fields
            logger.error("Unable to update the user: %s", e.__cause__)
            sentry_sdk.capture_exception(e)
            # Take care to refresh the user...

    return user, created


def france_connect_callback(request):
    # state is also available and should be checked (#1)
    code = request.GET.get("code")
    if code is None:
        return JsonResponse(
            {"message": "The query doesn't provide the 'code' parameter."}, status=400
        )

    data = {
        "client_id": settings.FRANCE_CONNECT_CLIENT_ID,
        "client_secret": settings.FRANCE_CONNECT_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.FRANCE_CONNECT_URL_CALLBACK,
    }
    logger.info(settings.FRANCE_CONNECT_URLS["token"])
    response = requests.post(settings.FRANCE_CONNECT_URLS["token"], data=data)
    if response.status_code != 200:
        message = "Unable to get the token from France Connect."
        logger.error(message)
        sentry_sdk.capture_message("%s\n%s" % (message, response.content))
        # The response is certainly ignored by FC but it's convenient for our tests
        return JsonResponse({"message": message}, status=response.status_code)

    # Contains access_token, token_type, expires_in, id_token
    # id_token contains a field 'nonce' to check (#2)
    token_data = response.json()
    # A token has been provided so it's time to fetch associated user infos
    # because the token is only valid for 5 seconds.
    logger.info(token_data)
    logger.info(settings.FRANCE_CONNECT_URLS["userinfo"])
    response = requests.get(
        settings.FRANCE_CONNECT_URLS["userinfo"],
        params={"schema": "openid"},
        headers={"Authorization": "Bearer " + token_data["access_token"]},
    )
    if response.status_code != 200:
        message = "Unable to get the user infos from France Connect."
        logger.error(message)
        sentry_sdk.capture_message(message)
        return JsonResponse({"message": message}, status=response.status_code)

    try:
        user_infos = json.loads(response.content.decode("utf-8"))
    except json.decoder.JSONDecodeError:
        return JsonResponse(
            {"message": "Unable to decode user infos from response."}, status=400
        )

    user, created = create_or_update_user(user_infos)
    if created:
        logger.info("New user created '%s'.", user.email)

    # Return JWT with id_token to allow logout from FC
    if user is None:
        return JsonResponse({"message": "No user"})

    return JsonResponse(
        {
            "token_type": token_data.get("token_type", ""),
            "token": jwt_auth_forms.json_web_token_encode_payload(user),
            # FIXME To check
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
            "post_logout_redirect_uri": settings.HTTPS_WEBSITE,
        }
        response = requests.get(settings.FRANCE_CONNECT_URLS["logout"], params=data)
        if response.status_code != 302:
            message = "Impossible de se déconnecter de France Connect."
            logger.error(message)
            sentry_sdk.capture_message(message)
            return JsonResponse({"message": message}, status=response.status_code)

    return JsonResponse({"message": "L'utilisateur est déconnecté."})
