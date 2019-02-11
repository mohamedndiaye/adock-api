from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.carrier_search, name="carriers_search"),
    path("<str:carrier_siret>/", views.carrier_detail, name="carriers_detail"),
    path(
        "<str:carrier_siret>/confirm_email/<token>/",
        views.carrier_confirm_email,
        name="carriers_confirm_email",
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
