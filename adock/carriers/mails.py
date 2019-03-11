from django.conf import settings
from django.core.mail import mail_managers, send_mail

from . import tokens


def get_recipient_list_from_env(email):
    if settings.PREPRODUCTION:
        return (email for (name, email) in settings.MANAGERS)

    return (email,)


def get_message_of_changes(changed_fields, carrier_editable, validated_data):
    message = ""
    for field in changed_fields:
        message += "- {field} : {current_value} => {new_value}\n".format(
            field=field,
            current_value=getattr(carrier_editable, field),
            new_value=validated_data[field],
        )
    return message


def mail_carrier_to_old_email(changed_fields, carrier_editable, validated_data):
    carrier = carrier_editable.carrier
    subject = (
        "%sNotification de modification de votre fiche transporteur"
        % settings.EMAIL_SUBJECT_PREFIX
    )
    message = """
Votre fiche transporteur {http_client_url}transporteur/{siret}
est en cours de modification avec les changements suivants :

{changes}
Si vous n'êtes pas d'accord avec ces changements, veuillez contacter les responsables du site A Dock.

Cordialement,
L'équipe A Dock""".format(
        http_client_url=settings.HTTP_CLIENT_URL,
        siret=carrier.siret,
        changes=get_message_of_changes(
            changed_fields, carrier_editable, validated_data
        ),
    )
    recipient_list = get_recipient_list_from_env(carrier_editable.email)
    send_mail(
        subject,
        message,
        settings.SERVER_EMAIL,
        recipient_list,
        fail_silently=settings.DEBUG,
    )


def mail_carrier_editable_to_confirm(changed_fields, carrier_editable, validated_data):
    token = tokens.carrier_editable_token.make_token(carrier_editable)
    subject = (
        "%sEn attente de confirmation de votre fiche transporteur"
        % settings.EMAIL_SUBJECT_PREFIX
    )
    message = """
Merci d'avoir renseigné votre fiche sur A Dock, l'application
qui facilite la relation chargeur et transporteur.

Pour confirmer les changements suivant sur votre fiche :

{changes}
Cliquez sur ce lien :

{http_client_url}transporteur/changement/{carrier_editable_id}/confirmer/{token}/

Cordialement,
L'équipe A Dock
    """.format(
        http_client_url=settings.HTTP_CLIENT_URL,
        carrier_editable_id=carrier_editable.id,
        token=token,
        changes=get_message_of_changes(
            changed_fields, carrier_editable, validated_data
        ),
    )
    recipient_list = get_recipient_list_from_env(
        validated_data.get("email", carrier_editable.email)
    )
    send_mail(
        subject,
        message,
        settings.SERVER_EMAIL,
        recipient_list,
        fail_silently=settings.DEBUG,
    )


def mail_managers_carrier_changes(changed_fields, carrier_editable, validated_data):
    # Send a mail to managers to track changes
    # The URL is detail view of the front application
    carrier = carrier_editable.carrier
    subject = "Modification du transporteur %s" % carrier.siret
    message = """
Modification en cours du transporteur : {enseigne}
SIRET : {siret}
{http_client_url}transporteur/{siret}

Informations modifiées :
""".format(
        enseigne=carrier.enseigne,
        siret=carrier.siret,
        http_client_url=settings.HTTP_CLIENT_URL,
    )

    message += get_message_of_changes(changed_fields, carrier_editable, validated_data)
    mail_managers(subject, message, fail_silently=True)


def mail_managers_carrier_confirmed(carrier_editable):
    carrier = carrier_editable.carrier
    subject = "La modification du transporteur %s est confirmée." % carrier.siret
    message = """
        Transporteur modifié : {enseigne}
        SIRET : {siret}
        {http_client_url}transporteur/{siret}
    """.format(
        enseigne=carrier.enseigne,
        siret=carrier.siret,
        http_client_url=settings.HTTP_CLIENT_URL,
    )
    mail_managers(subject, message, fail_silently=True)
