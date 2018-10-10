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
from django.conf import settings
from django.urls import include, path

from adock.meta import views as meta_views
from adock.selftest import views as selftest_views

urlpatterns = [
    path('transporteurs/', include('adock.transporteurs.urls')),
    path('meta/', meta_views.meta_index, name='meta'),
]

if settings.USE_SELFTEST:
    urlpatterns.append(
        path('selftest', selftest_views.selftest_index, name='selftest')
    )
