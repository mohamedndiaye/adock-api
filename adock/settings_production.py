DEBUG = False
USE_DEBUG_CONSOLE = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': PROJECT,
        'USER': 'deploy',
        # For logs
        'OPTIONS': {
            'application_name': PROJECT
        },
    }
}

EMAIL_HOST = 'localhost'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 25

ADMINS = (
    (u"Name", 'contact@example.com'),
)
MANAGERS = ADMINS

SERVER_NAME = 'foo.example.com'
SERVER_EMAIL = 'no-reply@' + SERVER_NAME

CORS_ORIGIN_WHITELIST = (
    SERVER_NAME,
)
ALLOWED_HOSTS = [SERVER_NAME]
SECRET_KEY = ''
