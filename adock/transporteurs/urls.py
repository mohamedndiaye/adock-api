from django.urls import path

from . import views

urlpatterns = [
    path('recherche/', views.search, name='transporteurs_recherche'),
    path('<str:transporteur_siret>/', views.transporteur_detail, name='transporteurs_detail'),
    path('<str:transporteur_siret>/confirmer_adresse/<token>/', views.transporteur_confirm_email, name='transporteurs_confirm_email'),
]
