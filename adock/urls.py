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
from django.urls import include, path

from adock.meta import views as meta_views
from adock.stats import views as stats_views
from adock.selftest import views as selftest_views

urlpatterns = [
    path("accounts/", include("adock.accounts.urls")),
    path("carriers/", include("adock.carriers.urls")),
    path("meta/", meta_views.meta_index, name="meta"),
    path("selftest/", selftest_views.selftest_index, name="selftest"),
    path("stats/", stats_views.stats, name="stats"),
]
