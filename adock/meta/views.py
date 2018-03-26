from django.http import JsonResponse
from django.views.decorators.cache import cache_page

from ..transporteurs import models as transporteurs_models


@cache_page(3600)
def meta_index(request):
    choices = {
        'WORKING_AREA_CHOICES': dict(transporteurs_models.WORKING_AREA_CHOICES)
    }

    return JsonResponse({
        'choices': choices
    })
