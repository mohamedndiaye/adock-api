import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Transporteur
from .forms import SubscriptionForm

@csrf_exempt
@require_POST
def subscribe(request):
    payload = json.loads(request.body.decode("utf-8"))
    # Get existing transporteur if any
    transporteur = Transporteur.objects.filter(siret=payload['siret']).first()
    form = SubscriptionForm(payload, instance=transporteur)
    if form.is_valid():
        transporteur = form.save()
        return JsonResponse({
            'id': transporteur.id,
        })
    else:
        return JsonResponse(form.errors, status=400)
