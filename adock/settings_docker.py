DEBUG = True
USE_DEBUG_CONSOLE = True
USE_RAVEN = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',  # pylint: disable=E0602
        'USER': 'postgres',
        'HOST': 'db',
        'PORT': '5432',
        # For logs
        'OPTIONS': {
            'application_name': 'adock'  # pylint: disable=E0602
        },
    }
}

EMAIL_PORT = 1025

ADMINS = (
    (u"Name", 'test@example.com'),
)
MANAGERS = ADMINS
