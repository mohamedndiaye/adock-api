PREPRODUCTION = True
STATIC_URL = "/api/static/"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "adock",
        "USER": "deploy",
        # For logs
        "OPTIONS": {"application_name": "adock"},
    }
}

ADMINS = (("Stéphane Raimbault", "stephane.raimbault@webstack.fr"),)

MANAGERS = ADMINS

HOSTNAME = "adock.webstack.fr"
HTTP_CLIENT_URL = "https://" + HOSTNAME + "/"
HTTP_SERVER_URL = "https://" + HOSTNAME + "/api/"

EMAIL_SUBJECT_PREFIX = "[A Dock preprod] "
SERVER_EMAIL = "no-reply@" + HOSTNAME

# Web tool or ./manage.py generate_secret_key with Django extensions
SECRET_KEY = ""

SENTRY_DSN = "https://URL-TO-PASTE-FROM-SENTRY-IO"

# https://partenaires.franceconnect.gouv.fr/monprojet/
FRANCE_CONNECT_URL_ROOT = "https://fcp.integ01.dev-franceconnect.fr/api/v1/"
FRANCE_CONNECT_CLIENT_ID = ""
FRANCE_CONNECT_CLIENT_SECRET = ""
