DEBUG = False
USE_DEBUG_CONSOLE = False
USE_DJANGO_EXTENSIONS = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': PROJECT,  # noqa
        'USER': 'deploy',
        # For logs
        'OPTIONS': {
            'application_name': PROJECT  # noqa
        },
    }
}

EMAIL_PORT = 25

STATIC_URL = '/api/static/'

ADMINS = (
    (u"Name", 'contact@example.com'),
)
MANAGERS = ADMINS

SERVER_NAME = WEBSITE
SERVER_EMAIL = 'no-reply@' + SERVER_NAME

CORS_ORIGIN_WHITELIST = (
    SERVER_NAME,
)
ALLOWED_HOSTS = [SERVER_NAME]
SECRET_KEY = ''
