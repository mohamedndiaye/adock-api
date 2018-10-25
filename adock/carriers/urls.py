from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.search, name="carriers_search"),
    path("stats/", views.get_stats, name="carriers_stats"),
    path("<str:carrier_siret>/", views.carrier_detail, name="carriers_detail"),
    path(
        "<str:carrier_siret>/confirmer_adresse/<token>/",
        views.carrier_confirm_email,
        name="carriers_confirmer_adresse",
    ),
    path(
        "<str:carrier_siret>/envoyer_code/",
        views.carrier_send_edit_code,
        name="carriers_envoyer_code",
    ),
]
