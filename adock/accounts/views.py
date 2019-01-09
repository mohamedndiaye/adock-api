import requests

from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.http import urlencode
from django.views.decorators.http import require_GET, require_POST
import sentry_sdk

from . import models as accounts_models

logger = logging.getLogger(__name__)


def france_connect_authorize(request):
    # Possible to set acr_values=eidas1 (eidas2 or eidas3) to filter on provider
    # of identities on a security level.
    data = {
        "client_id": settings.FRANCE_CONNECT_CLIENT_ID,
        # FIXME nonce should be tied to the user request (CSRF?) and checked in provided id token (cf #2)
        "nonce": "test",
        "redirect_uri": settings.FRANCE_CONNECT_URL_CALLBACK,
        "response_type": "code",
        "scope": "openid identite_pivot address phone",
        # FIXME state should be random or CSRF? and checcked (cf #1)
        "state": "test",
    }
    return HttpResponseRedirect(
        settings.FRANCE_CONNECT_URLS["authorize"] + "?" + urlencode(data)
    )


@require_GET
def france_connect_callback(request):
    # state is also available and should be checked (#1)
    code = request.GET["code"]

    data = {
        "client_id": settings.FRANCE_CONNECT_CLIENT_ID,
        "client_secret": settings.FRANCE_CONNECT_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.FRANCE_CONNECT_URL_CALLBACK,
    }
    response = requests.post(settings.FRANCE_CONNECT_URLS["token"], data=data)
    if response.status_code == 200:
        # Contains access_token, token_type, expires_in, id_token
        # id_token contains a field 'nonce' to check (#2)
        token_data = response.json()
        # A token has been provided so it's time to fetch associated user infos
        # because the token is only valid for 5 seconds.
        requests.get(
            settings.FRANCE_CONNECT_URLS["userinfo"],
            params={"schema": "openid"},
            headers={
                "headers": {"Authorization": "Bearer " + token_data["access_token"]}
            },
        )
        # given_name
        # family_name
        # birthdate
        # gender
        # birthplace
        # birthcountry
        # FIXME Store in DB?


@require_POST
def france_connect_logout(request):
    # FIXME To extract from JWT
    id_token = None
    data = {
        "id_token_hint": id_token,
        "state": "test",
        "post_logout_redirect_uri": "https://" + settings.WEBSITE,
    }
    return HttpResponseRedirect(
        settings.FRANCE_CONNECT_URLS["logout"] + "?" + urlencode(data)
    )
