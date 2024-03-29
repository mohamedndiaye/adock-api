# pylint: disable=W0614
import datetime
import os

PROJECT = "adock"
VERSION = "2.3.0"

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "ikc26ecc!xo8kck_8+_il6)m-^px@weoi6tq_1t+(50ar896h3"

DEBUG = False

# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "corsheaders",
    "rest_framework",
    "phonenumber_field",
    "adock.accounts.apps.AccountsConfig",
    "adock.carriers.apps.CarriersConfig",
    "adock.meta.apps.MetaConfig",
    "adock.selftest.apps.SelftestConfig",
    "adock.stats.apps.StatsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "jwt_auth.middleware.JWTAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "adock.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"environment": "adock.core.jinja2.environment"},
    }
]

WSGI_APPLICATION = "adock.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": PROJECT,
        # For logs
        "OPTIONS": {"application_name": PROJECT},
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "fr-fr"

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

LOGIN_URL = "accounts_log_in"

DATAFILES_ROOT = os.path.join(BASE_DIR, "datafiles")

HOSTNAME = "adock.beta.gouv.fr"
HTTP_CLIENT_URL = "https://" + HOSTNAME + "/"
HTTP_SERVER_URL_ENDPOINT = "/api/"
HTTP_SERVER_URL = "https://" + HOSTNAME + HTTP_SERVER_URL_ENDPOINT

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = False
CORS_ORIGIN_WHITELIST = None
ALLOWED_HOSTS = None

PHONENUMBER_DB_FORMAT = "NATIONAL"
PHONENUMBER_DEFAULT_REGION = "FR"

EMAIL_SUBJECT_PREFIX = "[A Dock] "
EMAIL_HOST = "localhost"
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_TIMEOUT = 5

CARRIERS_LIMIT = 200

# Validity of token to confirm email address
PASSWORD_RESET_TIMEOUT_DAYS = 2
CARRIER_EDIT_CODE_TIMEOUT_MINUTES = 60
CARRIER_EDIT_CODE_INTERVAL = datetime.timedelta(
    minutes=CARRIER_EDIT_CODE_TIMEOUT_MINUTES
)

# PRODUCTION, PREPRODUCTION, DEVELOPMENT or E2E
ENVIRONMENT = "PRODUCTION"

USE_DEBUG_CONSOLE = False
USE_DJANGO_EXTENSIONS = False
USE_SENTRY = True
USE_CIRCLECI = False

SENTRY_DSN = ""

JWT_EXPIRATION_DELTA = datetime.timedelta(seconds=3600)
JWT_PAYLOAD_HANDLER = "adock.accounts.jwt.jwt_payload_handler"

# https://partenaires.franceconnect.gouv.fr/
FRANCE_CONNECT_URL_ROOT = "https://app.franceconnect.gouv.fr/api/v1/"
FRANCE_CONNECT_CLIENT_ID = ""
FRANCE_CONNECT_CLIENT_SECRET = ""

NGINX_ACCESS_LOG = "/var/log/adock.beta.gouv.fr/access.log"

try:
    from .settings_local import *  # pylint: disable=W0401
except ImportError:  # pragma: no cover
    pass

FRANCE_CONNECT_URLS = {
    "authorize": FRANCE_CONNECT_URL_ROOT + "authorize",
    "token": FRANCE_CONNECT_URL_ROOT + "token",
    "userinfo": FRANCE_CONNECT_URL_ROOT + "userinfo",
    "logout": FRANCE_CONNECT_URL_ROOT + "logout",
}
FRANCE_CONNECT_URL_CALLBACK = HTTP_CLIENT_URL + "fc/callback/"
FRANCE_CONNECT_URL_POST_LOGOUT = HTTP_CLIENT_URL + "fc/postlogout/"

if not CORS_ORIGIN_WHITELIST:
    CORS_ORIGIN_WHITELIST = (HTTP_CLIENT_URL[:-1],)

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = [HOSTNAME]

SERVER_EMAIL = "contact@" + HOSTNAME
DREAL_EMAIL = "registre-transports.bretagne@developpement-durable.gouv.fr"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(levelname)s %(asctime)s %(message)s"}},
    "handlers": {
        "output": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "filename": "/var/log/" + PROJECT + "/django.log",
            "formatter": "simple",
        }
    },
    "loggers": {PROJECT: {"handlers": ["output"], "level": "DEBUG"}},
}

if USE_DEBUG_CONSOLE:
    LOGGING["handlers"]["output"] = {"class": "logging.StreamHandler", "level": "DEBUG"}

if USE_DJANGO_EXTENSIONS:
    INSTALLED_APPS += ("django_extensions",)

if USE_SENTRY:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(SENTRY_DSN, integrations=[DjangoIntegration()], release=VERSION)
