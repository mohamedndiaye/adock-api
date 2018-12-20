from django.contrib.auth import views as auth_views
from django.urls import path
from jwt_auth import views as jwt_auth_views


urlpatterns = [
    path("login/", jwt_auth_views.obtain_jwt_token, name="accounts_log_in"),
    path(
        "logout/", auth_views.LogoutView.as_view(next_page="/"), name="accounts_log_out"
    ),
]
