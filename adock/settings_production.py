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

ADMINS = ((u"Stéphane Raimbault", "stephane.raimbault@webstack.fr"),)

MANAGERS = (
    ("Stéphane Raimbault", "stephane.raimbault@webstack.fr"),
    ("Alexandre Dupont", "alexandre.dupont@developpement-durable.gouv.fr"),
    ("Clémence Gourragne", "clemence.gourragne@beta.gouv.fr"),
)

# Web tool or ./manage.py generate_secret_key with Django extensions
SECRET_KEY = ""

SENTRY_DSN = "https://URL-TO-PASTE-FROM-SENTRY-IO"

# https://partenaires.franceconnect.gouv.fr/
FRANCE_CONNECT_CLIENT_ID = ""
FRANCE_CONNECT_CLIENT_SECRET = ""
