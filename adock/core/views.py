import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Carrier
from .forms import SubscriptionForm

@csrf_exempt
@require_POST
def subscribe(request):
    payload = json.loads(request.body.decode("utf-8"))
    # Get existing carrier if any
    carrier = Carrier.objects.filter(siret=payload['siret']).first()
    form = SubscriptionForm(payload, instance=carrier)
    if form.is_valid():
        carrier = form.save()
        return JsonResponse({
            'id': carrier.id,
        })
    else:
        return JsonResponse(form.errors, status=400)
