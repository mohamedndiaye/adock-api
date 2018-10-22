PREPRODUCTION = True
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

SENTRY_DSN = 'https://URL-TO-PASTE-FROM-SENTRY-IO'
