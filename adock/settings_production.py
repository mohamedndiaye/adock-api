import os
import raven

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': PROJECT,  # pylint: disable=E0602
        'USER': 'deploy',
        # For logs
        'OPTIONS': {
            'application_name': PROJECT  # pylint: disable=E0602
        },
    }
}

EMAIL_PORT = 25

STATIC_URL = '/api/static/'

ADMINS = (
    (u"Name", 'contact@example.com'),
)
MANAGERS = ADMINS

SERVER_NAME = WEBSITE  # pylint: disable=E0602
SERVER_EMAIL = 'no-reply@' + SERVER_NAME

CORS_ORIGIN_WHITELIST = (
    SERVER_NAME,
)
ALLOWED_HOSTS = [SERVER_NAME]
SECRET_KEY = ''

RAVEN_CONFIG = {
    'dsn': 'https://URL-TO-PASTE-FROM-SENTRY-IO',
    'release': raven.fetch_git_sha(os.path.dirname(os.pardir)),
}
