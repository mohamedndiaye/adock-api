from django.urls import path

from . import views

urlpatterns = [
    path('recherche/', views.search, name='transporteurs_recherche'),
    path('<str:transporteur_siret>/', views.transporteur_detail, name='transporteurs_detail'),
]
