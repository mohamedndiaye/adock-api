from django.conf import settings
from django.http.response import JsonResponse


def user_is_staff():
    def decorated(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if settings.AUTHENTICATION_DISABLED or (
                request.user and request.user.is_staff
            ):
                return view_func(request, *args, **kwargs)
            return JsonResponse({"message": "Not Allowed"}, status=405)

        return _wrapped_view

    return decorated


def user_required():
    def decorated(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if settings.AUTHENTICATION_DISABLED or not request.user.is_anonymous:
                return view_func(request, *args, **kwargs)
            return JsonResponse({"message": "Not Allowed"}, status=405)

        return _wrapped_view

    return decorated
