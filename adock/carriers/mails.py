from django.conf import settings
from django.core.mail import mail_managers, send_mail
from django.utils import timezone

from . import tokens


def get_recipient_list_from_env(carrier):
    if settings.PREPRODUCTION:
        return (email for (name, email) in settings.MANAGERS)

    return (carrier.email,)


def mail_carrier_to_confirm_email(carrier):
    if not carrier.email:
        return

    token = tokens.email_confirmation_token.make_token(carrier)
    subject = (
        "%sConfirmation de l'adresse électronique du transporteur"
        % settings.EMAIL_SUBJECT_PREFIX
    )
    message = """
Merci d'avoir renseigné votre fiche sur A Dock, l'application
qui facilite la relation chargeur et transporteur.

Cliquez sur le lien pour confirmer votre adresse électronique « {email} »
et ainsi sécuriser la fiche transporteur :

{http_client_url}transporteur/{siret}/confirm/{token}/

Cordialement,
L'équipe A Dock
    """.format(
        http_client_url=settings.HTTP_CLIENT_URL,
        siret=carrier.siret,
        email=carrier.email,
        token=token,
    )
    recipient_list = get_recipient_list_from_env(carrier)
    send_mail(
        subject,
        message,
        settings.SERVER_EMAIL,
        recipient_list,
        fail_silently=settings.DEBUG,
    )


def mail_managers_changes(carrier, old_data_changed):
    # Send a mail to managers to track changes
    # The URL is detail view of the front application
    subject = "Modification du transporteur %s" % carrier.siret
    message = """
Modification du transporteur : {enseigne}
SIRET : {siret}
{http_client_url}transporteur/{siret}

Valeurs modifiées :
    """.format(
        enseigne=carrier.enseigne,
        siret=carrier.siret,
        http_client_url=settings.HTTP_CLIENT_URL,
    )

    for field, old_value in old_data_changed.items():
        message += "\n- {field} : {old_value} => {new_value}".format(
            field=field, old_value=old_value, new_value=getattr(carrier, field)
        )
    mail_managers(subject, message, fail_silently=True)


def mail_managers_lock(carrier):
    subject = "Verrouillage du transporteur %s" % carrier.siret
    message = """
Verrouillage du transporteur : {enseigne}
SIRET : {siret}
{http_client_url}transporteur/{siret}

Adresse électronique confirmée : {email}
    """.format(
        enseigne=carrier.enseigne,
        siret=carrier.siret,
        http_client_url=settings.HTTP_CLIENT_URL,
        email=carrier.email,
    )
    mail_managers(subject, message, fail_silently=True)


def mail_carrier_edit_code(carrier):
    subject = "%sCode de modification" % settings.EMAIL_SUBJECT_PREFIX
    max_edit_time = carrier.edit_code_at + settings.CARRIER_EDIT_CODE_INTERVAL
    message = """
Votre code de modification est {edit_code}.

Ce code vous permet de modifier la fiche du transporteur « {enseigne} » jusqu'à {max_edit_time_display}.

Cordialement,
L'équipe A Dock
    """.format(
        enseigne=carrier.enseigne,
        edit_code=carrier.edit_code,
        max_edit_time_display=timezone.localtime(max_edit_time).strftime(
            "%H:%M (%d/%m/%Y)"
        ),
    )
    recipient_list = get_recipient_list_from_env(carrier)
    send_mail(
        subject,
        message,
        settings.SERVER_EMAIL,
        recipient_list,
        fail_silently=settings.DEBUG,
    )
