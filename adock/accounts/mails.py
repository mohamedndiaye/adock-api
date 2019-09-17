from django.conf import settings
from django.core.mail import mail_managers

from ..core import mails as core_mails
from . import tokens as accounts_tokens
from ..carriers import tokens as carriers_tokens


def mail_user_to_activate(user):
    # The link triggers the UI that requests the backend to provide feedback to
    # the user.
    token = accounts_tokens.account_token_generator.make_token(user)

    subject = (
        "%sActivez votre compte utilisateur A Dock" % settings.EMAIL_SUBJECT_PREFIX
    )
    message = """
Bonjour,

Vous venez de créer un compte utilisateur sur A Dock, il suffit maintenant de cliquer sur ce lien pour l'activer :

{http_client_url}utilisateur/{user_id}/activer/{token}/

Un message de notification a également été envoyé à l’entreprise à laquelle vous êtes associé.

En vous remerciant de l’intérêt que vous portez pour A Dock, l’outil de simplification des relations dans le transport de marchandises par route !

{signature}
""".format(
        http_client_url=settings.HTTP_CLIENT_URL,
        signature=core_mails.SIGNATURE,
        token=token,
        user_id=user.pk,
    )

    user.email_user(
        subject=subject,
        message=message,
        from_email=settings.SERVER_EMAIL,
        fail_silently=settings.DEBUG,
    )


def mail_user_to_activate_with_carrier_editable(
    user, changed_fields, current_carrier_editable, new_carrier_editable
):
    user_token = accounts_tokens.account_token_generator.make_token(user)
    carrier_editable_token = carriers_tokens.carrier_editable_token_generator.make_token(
        new_carrier_editable
    )
    subject = (
        "%sEn attente de confirmation de votre compte et vos modifications"
        % settings.EMAIL_SUBJECT_PREFIX
    )
    message = """
Merci d'avoir créé votre compte utilisateur sur A Dock.
Il suffit maintenant de cliquer sur ce lien pour activer et confirmer les modifications
de la fiche transporteur :

{http_client_url}utilisateur/{user_id}/activer/{user_token}/transporteur/changement/{new_carrier_editable_id}/confirmer/{carrier_editable_token}/

{signature}
""".format(
        carrier_editable_token=carrier_editable_token,
        http_client_url=settings.HTTP_CLIENT_URL,
        new_carrier_editable_id=new_carrier_editable.id,
        signature=core_mails.SIGNATURE,
        user_id=user.pk,
        user_token=user_token,
    )
    user.email_user(
        subject=subject,
        message=message,
        from_email=settings.SERVER_EMAIL,
        fail_silently=settings.DEBUG,
    )


def mail_user_to_recover_password(user, token):
    subject = "%sRécupération de mot de passe" % settings.EMAIL_SUBJECT_PREFIX
    message = """
Vous avez demander la récupération du mot de passe de votre compte A Dock, si vous n'êtes pas à l'origine
de la demande vous pouvez ignorer ce message sinon vous pouvez cliquer sur le lien :

{http_client_url}utilisateur/{email}/reinitialiser/{token}/

{signature}
""".format(
        http_client_url=settings.HTTP_CLIENT_URL,
        email=user.email,
        token=token,
        signature=core_mails.SIGNATURE,
    )
    user.email_user(
        subject=subject,
        message=message,
        from_email=settings.SERVER_EMAIL,
        fail_silently=settings.DEBUG,
    )


def mail_managers_new_account(user, send_activation_link=False):
    subject = "log - Nouveau compte utilisateur %s" % user.email
    message_activation_link_sent = (
        "Un courriel d'activation a été envoyé au moment de la création."
    )
    message = """
Le nouveau compte utilisateur est :
- {username}
- {email}
- {first_name} {last_name}

Créé via {provider_display}.
{message_activation_link}
""".format(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        provider_display=user.get_provider_display(),
        message_activation_link=message_activation_link_sent
        if send_activation_link
        else "",
    )
    mail_managers(subject, message, fail_silently=True)
