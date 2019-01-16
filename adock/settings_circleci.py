DEBUG = True
USE_DEBUG_CONSOLE = True
USE_SENTRY = False
USE_CIRCLECI = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "circleci_test",
        "HOST": "127.0.0.1",
        "PORT": "5432",
        # For logs
        "OPTIONS": {"application_name": "adock"},
    }
}

EMAIL_PORT = 1025

ADMINS = ((u"Name", "test@example.com"),)
MANAGERS = ADMINS
