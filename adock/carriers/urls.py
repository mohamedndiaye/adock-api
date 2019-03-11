from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.carrier_search, name="carriers_search"),
    path("<str:carrier_siret>/", views.carrier_detail, name="carriers_detail"),
    path(
        "editable/<int:carrier_editable_id>/confirm/<str:token>/",
        views.carrier_editable_confirm,
        name="carriers_carrier_editable_confirm",
    ),
    # POST to create SQL entry and GET to generate PDF
    path(
        "<str:carrier_siret>/certificate/",
        views.certificate_detail,
        name="carriers_certificate_detail",
    ),
    # GET to generate HTML
    path(
        "<str:carrier_siret>/certificate/html/",
        views.certificate_detail,
        name="carriers_certificate_detail_html",
        kwargs={"as_pdf": False},
    ),
    path(
        "certificate/<int:certificate_id>/confirm/<str:token>",
        views.certificate_confirm,
        name="carriers_certificate_confirm",
    ),
]
