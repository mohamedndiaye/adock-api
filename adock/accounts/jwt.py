from django.utils import timezone
from django.conf import settings


def jwt_payload_handler(user):
    """Custom payload handler"""
    return {
        "user_id": user.pk,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
        "exp": timezone.now() + settings.JWT_EXPIRATION_DELTA,
    }
