from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.search, name="carriers_search"),
    path("stats/", views.get_stats, name="carriers_stats"),
    path("<str:carrier_siret>/", views.carrier_detail, name="carriers_detail"),
    path(
        "<str:carrier_siret>/confirm_email/<token>/",
        views.carrier_confirm_email,
        name="carriers_confirm_email",
    ),
    path(
        "<str:carrier_siret>/send_code/",
        views.carrier_send_edit_code,
        name="carriers_send_code",
    ),
]
