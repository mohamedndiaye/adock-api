DEBUG = True
USE_DEBUG_CONSOLE = True
USE_DJANGO_EXTENSIONS = True
USE_SENTRY = False

# PRODUCTION, PREPRODUCTION or DEVELOPMENT
ENVIRONMENT = "DEVELOPMENT"
if ENVIRONMENT == "E2E":
    print("WARNING: Running with environment set to E2E.")

HOSTNAME = "localhost"
HTTP_SERVER_URL = "http://" + HOSTNAME + ":8000/"
HTTP_CLIENT_URL = "http://" + HOSTNAME + ":8080/"

CORS_ORIGIN_WHITELIST = (HTTP_CLIENT_URL[:-1],)

EMAIL_PORT = 1025

ADMINS = ((u"Name", "contact@example.com"),)
MANAGERS = ADMINS

# Speed up tests
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

# https://partenaires.franceconnect.gouv.fr/
FRANCE_CONNECT_URL_ROOT = "https://fcp.integ01.dev-franceconnect.fr/api/v1/"
FRANCE_CONNECT_CLIENT_ID = ""
FRANCE_CONNECT_CLIENT_SECRET = ""
