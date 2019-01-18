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

WEBSITE = "adock.webstack.fr"
HTTPS_WEBSITE = "https://" + WEBSITE
SERVER_EMAIL = "no-reply@" + WEBSITE
EMAIL_SUBJECT_PREFIX = "[adock-preprod]"

CORS_ORIGIN_WHITELIST = (WEBSITE,)
ALLOWED_HOSTS = [WEBSITE]
# Web tool or ./manage.py generate_secret_key with Django extensions
SECRET_KEY = ""

SENTRY_DSN = "https://URL-TO-PASTE-FROM-SENTRY-IO"

FRANCE_CONNECT_CLIENT_ID = ""
FRANCE_CONNECT_CLIENT_SECRET = ""
FRANCE_CONNECT_URL_CALLBACK = HTTPS_WEBSITE + "/fc/callback/"
