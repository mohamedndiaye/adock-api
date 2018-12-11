DEBUG = True
USE_DEBUG_CONSOLE = True
USE_DJANGO_EXTENSIONS = True
USE_SENTRY = False

WEBSITE = "localhost:8080"
CORS_ORIGIN_WHITELIST = (WEBSITE,)

EMAIL_PORT = 1025

ADMINS = ((u"Name", "contact@example.com"),)
MANAGERS = ADMINS

# To copy/paste from integration
FRANCE_CONNECT_CLIENT_ID = ""
FRANCE_CONNECT_CLIENT_SECRET = ""
# According to your ngrok like URL...
FRANCE_CONNECT_URL_CALLBACK = "https://adock.beta.gouv.fr/accounts/fc/callback/"
