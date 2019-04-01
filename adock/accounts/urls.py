from django.urls import path
from jwt_auth import views as jwt_auth_views

from . import views

urlpatterns = [
    path("create/", views.account_create, name="accounts_create"),
    path(
        "<int:user_id>/activate/<str:token>/",
        views.account_activate,
        name="accounts_activate",
    ),
    path("login/", jwt_auth_views.jwt_token, name="accounts_log_in"),
    path("profile/", views.account_profile, name="accounts_profile"),
    path(
        "profile/extended/",
        views.account_profile,
        name="accounts_profile_extended",
        kwargs={"extended": True},
    ),
    path(
        "fc/authorize/", views.france_connect_authorize, name="france_connect_authorize"
    ),
    path("fc/callback/", views.france_connect_callback, name="france_connect_callback"),
    path("fc/logout/", views.france_connect_logout, name="france_connect_logout"),
]
