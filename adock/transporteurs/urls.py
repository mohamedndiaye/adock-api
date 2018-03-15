from django.urls import path

from . import views

urlpatterns = [
    path('inscription/', views.subscribe, name='transporteurs_inscription'),
    path('recherche/', views.search, name='transporteurs_recherche'),
]
