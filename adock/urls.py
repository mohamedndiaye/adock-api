"""adock URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from .transporteurs import views as transporteurs_views
from .sirene import views as sirene_views

urlpatterns = [
    path('transporteurs/inscription/', transporteurs_views.subscribe, name='transporteurs_inscription'),
    path('sirene/recherche/', sirene_views.search, name='sirene_recherche'),
    path('admin/', admin.site.urls),
]
