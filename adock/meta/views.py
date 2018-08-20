import collections

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.cache import cache_page

from . import models as meta_models
from ..transporteurs import models as transporteurs_models


@cache_page(3600)
def meta_index(request):
    metas = meta_models.Meta.objects.all()
    data = {
        'choices': {
            'WORKING_AREA_CHOICES': collections.OrderedDict(transporteurs_models.WORKING_AREA_CHOICES),
            'SPECIALITY_CHOICES': collections.OrderedDict(transporteurs_models.SPECIALITY_CHOICES),
            'OBJECTIF_CO2_CHOICES': collections.OrderedDict(transporteurs_models.OBJECTIF_CO2_CHOICES)
        },
        'version': settings.VERSION,
    }
    for meta in metas:
        data[meta.name] = meta.data

    return JsonResponse(data)
