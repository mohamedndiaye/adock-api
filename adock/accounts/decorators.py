from django.conf import settings
from django.http.response import JsonResponse


def user_is_staff():
    def decorated(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_staff:
                return view_func(request, *args, **kwargs)

            if request.user.is_anonymous:
                status_code = 401
            else:
                status_code = 403

            return JsonResponse({"message": "Forbidden"}, status=status_code)

        return _wrapped_view

    return decorated


def user_required():
    def decorated(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_anonymous:
                return view_func(request, *args, **kwargs)
            return JsonResponse({"message": "Unauthorized"}, status=401)

        return _wrapped_view

    return decorated
