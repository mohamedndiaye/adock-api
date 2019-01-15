from django.urls import path

from . import models, views

urlpatterns = [
    path("search/", views.search, name="carriers_search"),
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
    path(
        "<str:carrier_siret>/certificate/foreigners/",
        views.carrier_certificate,
        name="carriers_certificate_foreigners",
        kwargs={"kind": models.CERTIFICATE_FOREIGNERS},
    ),
    path(
        "<str:carrier_siret>/certificate/foreigners/html/",
        views.carrier_certificate,
        name="carriers_certificate_foreigners_html",
        kwargs={"kind": models.CERTIFICATE_FOREIGNERS, "as_pdf": False},
    ),
    path(
        "<str:carrier_siret>/certificate/no-foreigners/",
        views.carrier_certificate,
        name="carriers_certificate_no_foreigners",
        kwargs={"kind": models.CERTIFICATE_NO_FOREIGNERS},
    ),
    path(
        "<str:carrier_siret>/certificate/no-foreigners/html/",
        views.carrier_certificate,
        name="carriers_certificate_no_foreigners_html",
        kwargs={"kind": models.CERTIFICATE_NO_FOREIGNERS, "as_pdf": False},
    ),
]
