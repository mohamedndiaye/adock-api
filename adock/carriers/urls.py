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
    # POST to create SQL entry and GET to generate PDF
    path(
        "<str:carrier_siret>/certificate/",
        views.carrier_certificate,
        name="carriers_certificate",
    ),
    # GET to generate HTML
    path(
        "<str:carrier_siret>/certificate/html/",
        views.carrier_certificate,
        name="carriers_certificate_html",
        kwargs={"as_pdf": False},
    ),
]
