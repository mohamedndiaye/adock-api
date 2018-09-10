import os
import raven

STATIC_URL = '/api/static/'

ADMINS = (
    (u"Stéphane Raimbault", 'stephane.raimbault@webstack.fr'),
)

MANAGERS = (
    ("Stéphane Raimbault", 'stephane.raimbault@webstack.fr'),
    ("Alexandre Dupont", 'alexandre.dupont@developpement-durable.gouv.fr'),
)

SERVER_NAME = 'adock.beta.gouv.fr'
SERVER_EMAIL = 'no-reply@' + SERVER_NAME

CORS_ORIGIN_WHITELIST = (
    SERVER_NAME,
)
ALLOWED_HOSTS = [SERVER_NAME]
# Web tool or ./manage.py generate_secret_key with Django extensions
SECRET_KEY = ''

RAVEN_CONFIG = {
    'dsn': 'https://URL-TO-PASTE-FROM-SENTRY-IO',
    'release': raven.fetch_git_sha(os.path.dirname(os.pardir)),
}
