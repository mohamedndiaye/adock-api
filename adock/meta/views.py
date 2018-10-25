import collections

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.cache import cache_page

from . import models as meta_models
from ..carriers import models as carriers_models

# Exclude empty choice for working areas
META_WORKING_AREA_CHOICES = collections.OrderedDict(
    (k, v)
    for k, v in carriers_models.WORKING_AREA_CHOICES
    if k != carriers_models.WORKING_AREA_UNDEFINED
)
META_SPECIALITY_CHOICES = collections.OrderedDict(carriers_models.SPECIALITY_CHOICES)
META_OBJECTIF_CO2_CHOICES = collections.OrderedDict(
    carriers_models.OBJECTIF_CO2_CHOICES
)


@cache_page(3600)
def meta_index(request):
    metas = meta_models.Meta.objects.all()
    data = {
        "choices": {
            "WORKING_AREA_CHOICES": META_WORKING_AREA_CHOICES,
            "SPECIALITY_CHOICES": META_SPECIALITY_CHOICES,
            "OBJECTIF_CO2_CHOICES": META_OBJECTIF_CO2_CHOICES,
        },
        "version": settings.VERSION,
    }
    for meta in metas:
        data[meta.name] = meta.data

    return JsonResponse(data)
