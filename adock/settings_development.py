DEBUG = True
USE_DEBUG_CONSOLE = True
USE_DJANGO_EXTENSIONS = True
USE_SENTRY = False

WEBSITE = "localhost:8080"
HTTPS_WEBSITE = "http://" + WEBSITE
HTTP_SERVER_URL = "http://localhost:8000/"
HTTP_CLIENT_URL = "http://localhost:8080/"

# According to your ngrok or serveo URL...
# ssh -R 80:localhost:8000 serveo.net
PUBLIC_HOSTNAME = "foo.serveo.net"
CORS_ORIGIN_WHITELIST = (WEBSITE, PUBLIC_HOSTNAME)

EMAIL_PORT = 1025

ADMINS = ((u"Name", "contact@example.com"),)
MANAGERS = ADMINS

# Speed up tests
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

AUTHENTICATION_DISABLED = False

# To copy/paste from integration
FRANCE_CONNECT_CLIENT_ID = ""
FRANCE_CONNECT_CLIENT_SECRET = ""

FRANCE_CONNECT_URL_CALLBACK = "https://" + PUBLIC_HOSTNAME + "/accounts/fc/callback/"
