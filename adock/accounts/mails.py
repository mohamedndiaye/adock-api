from django.conf import settings
from django.core.mail import mail_managers


def mail_user_to_activate(user, token):
    # The link triggers the UI that requests the backend to provide feedback to
    # the user.
    subject = "%sConfirmation de votre adresse électronique"
    message = """
Vous venez de créer un compte utilisateur sur A Dock, il suffit maintenant de cliquer sur ce lien
pour l'activer :

{http_client_url}utilisateur/{user_id}/activer/{token}/

Cordialement,
L'équipe A Dock
    """.format(
        http_client_url=settings.HTTP_CLIENT_URL, user_id=user.pk, token=token
    )

    user.email_user(
        subject=subject,
        message=message,
        from_email=settings.SERVER_EMAIL,
        fail_silently=settings.DEBUG,
    )


def mail_user_to_recover_password(user, token):
    subject = "%sRécupération de mot de passe"
    message = """
Vous avez demander la récupération du mot de passe de votre compte A Dock, si vous n'êtes pas à l'origine
de la demande vous pouvez ignorer ce message sinon vous pouvez cliquer sur le lien :

{http_client_url}utilisateur/{email}/reinitialiser/{token}/

Cordialement,
L'équipe A Dock
""".format(
        http_client_url=settings.HTTP_CLIENT_URL, email=user.email, token=token
    )
    user.email_user(
        subject=subject,
        message=message,
        from_email=settings.SERVER_EMAIL,
        fail_silently=settings.DEBUG,
    )


def mail_managers_new_account(user):
    subject = "Nouveau compte utilisateur %s" % user.email
    message = """
Le nouveau compte utilisateur est :
- {username}
- {email}
- {first_name} {last_name}

Créé via {provider_display}
""".format(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        provider_display=user.get_provider_display(),
    )
    mail_managers(subject, message, fail_silently=True)
