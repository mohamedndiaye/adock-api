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

EMAIL_SUBJECT_PREFIX = "[A Dock preprod]"

# Web tool or ./manage.py generate_secret_key with Django extensions
SECRET_KEY = ""

SENTRY_DSN = "https://URL-TO-PASTE-FROM-SENTRY-IO"

FRANCE_CONNECT_CLIENT_ID = ""
FRANCE_CONNECT_CLIENT_SECRET = ""
FRANCE_CONNECT_URL_CALLBACK = HTTP_CLIENT_URL + "/fc/callback/"
