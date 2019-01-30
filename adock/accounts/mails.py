from django.conf import settings


def mail_user_to_activate(user, token):
    # The link triggers the UI that requests the backend to provide feedback to
    # the user.
    subject = "%sConfirmation de votre adresse électronique"
    message = """
Vous venez de créer un compte utilisateur sur A Dock, il suffit maintenant de cliquer sur ce lien
pour l'activer :

{http_server_url}/utilisateur/{user_id}/activer/{token}/

Cordialement,
L'équipe A Dock
    """.format(
        http_server_url=settings.HTTP_SERVER_URL, user_id=user.pk, token=token
    )

    user.email_user(
        subject=subject,
        message=message,
        from_email=settings.SERVER_EMAIL,
        fail_silently=settings.DEBUG,
    )
