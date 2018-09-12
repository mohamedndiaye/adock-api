import os
import raven

DEBUG = True

STATIC_URL = '/api/static/'

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
SECRET_KEY = ''

# Disable mails (or listen on local port)
EMAIL_PORT = 1025
