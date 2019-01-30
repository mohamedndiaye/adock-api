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
from jwt_auth import views as jwt_auth_views

from adock.core import views as core_views

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

    # The link triggers the UI that requests the backend to provide feedback to
    # the user.
    subject = "%sConfirmation de votre adresse électronique"
    message = """
Vous venez de créer un compte utilisateur sur A Dock, il suffit maintenant de cliquer sur ce lien
pour l'activer :

{http_server_url}/utilisateur/{user_id}/activer/{token}/

Cordialement,
L'équipe A Dock
    """.format(
        http_server_url=settings.HTTP_SERVER_URL, user_id=user.pk, token=token
    )

    user.email_user(
        subject=subject,
        message=message,
        from_email=settings.SERVER_EMAIL,
        fail_silently=settings.DEBUG,
    )
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


def france_connect_callback(request):
    # state is also available and should be checked (#1)
    code = request.GET.get("code")
    if code is None:
        return JsonResponse(
            {"message": "La requête ne contient pas le paramètre « code »."}, status=400
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
        message = "Impossible d'obtenir le jeton de France Connect."
        logger.error(message)
        sentry_sdk.capture_message("%s\n%s" % (message, response.content))
        # The response is certainly ignored by FC but it's convenient for our tests
        return JsonResponse({"message": message}, status=response.status_code)

    # Contains access_token, token_type, expires_in, id_token
    # id_token contains a field 'nonce' to check (#2)
    token_data = response.json()
    # A token has been provided so it's time to fetch associated user infos
    # because the token is only valid for 5 seconds.
    response = requests.get(
        settings.FRANCE_CONNECT_URLS["userinfo"],
        params={"schema": "openid"},
        headers={"Authorization": "Bearer " + token_data["access_token"]},
    )
    if response.status_code != 200:
        message = "Impossible d'obtenir les informations utilisateur de France Connect."
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
            {
                "message": "Le paramètre « sub » n'a pas été retourné par France Connect."
            },
            status=400,
        )

    user, created = create_or_update_user(user_infos)
    if created:
        logger.info("Nouvel utilisateur créé « %s ».", user.email)

    # Return JWT with id_token to allow logout from FC
    if user is None:
        return JsonResponse({"message": "Aucun utilisateur."})

    return JsonResponse(
        {
            "token_type": token_data.get("token_type", ""),
            "token": jwt_auth_views.jwt_encode_token(user),
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
