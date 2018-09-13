import os
import raven

STATIC_URL = '/api/static/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'adock',
        'USER': 'deploy',
        # For logs
        'OPTIONS': {
            'application_name': 'adock'
        },
    }
}

ADMINS = (
    (u"Stéphane Raimbault", 'stephane.raimbault@webstack.fr'),
)

MANAGERS = ADMINS

SERVER_NAME = 'adock.webstack.fr'
SERVER_EMAIL = 'no-reply@' + SERVER_NAME

CORS_ORIGIN_WHITELIST = (
    SERVER_NAME,
)
ALLOWED_HOSTS = [SERVER_NAME]
# Web tool or ./manage.py generate_secret_key with Django extensions
SECRET_KEY = ''

# Disable mails (or listen on local port)
EMAIL_PORT = 1025

RAVEN_CONFIG = {
    'dsn': 'https://URL-TO-PASTE-FROM-SENTRY-IO',
    'release': raven.fetch_git_sha(os.path.dirname(os.pardir)),
}
