from django.urls import path

from . import views

urlpatterns = [
    path('recherche/', views.search, name='transporteurs_recherche'),
    path('<str:transporteur_siret>/', views.transporteur_detail, name='transporteurs_detail'),
    path('<str:transporteur_siret>/confirmer_adresse/<token>/', views.transporteur_confirm_email, name='transporteurs_confirmer_adresse'),
    path('<str:transporteur_siret>/envoyer_code/', views.transporteur_send_code, name='transporteurs_envoyer_code'),
]
