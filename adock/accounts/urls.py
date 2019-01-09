from django.contrib.auth import views as auth_views
from django.urls import path
from jwt_auth import views as jwt_auth_views

from . import views

urlpatterns = [
    path("login/", jwt_auth_views.jwt_token, name="accounts_log_in"),
    path(
        "logout/", auth_views.LogoutView.as_view(next_page="/"), name="accounts_log_out"
    ),
    path(
        "fc/authorize/", views.france_connect_authorize, name="france_connect_authorize"
    ),
    path("fc/callback/", views.france_connect_callback, name="france_connect_callback"),
    path("fc/logout/", views.france_connect_logout, name="france_connect_logout"),
]
