import django
from django.http import JsonResponse


def get_csrf_token(request):
    token = django.middleware.csrf.get_token(request)
    return JsonResponse({"csrf_token": token})
