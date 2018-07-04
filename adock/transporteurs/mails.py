from django.conf import settings
from django.core.mail import mail_managers, send_mail

from . import tokens

def mail_transporteur_to_confirm_email(transporteur):
    if not transporteur.email:
        return

    token = tokens.email_confirmation_token.make_token(transporteur)
    subject = "A Dock - Confirmation de votre adresse électronique"
    message = """
Merci d'avoir renseigné votre fiche sur A Dock, l'application
qui facilite la relation chargeur et transporteur.

https://{website}/transporteur/{siret}

Pour confirmer votre adresse électronique « {email} »
et ainsi sécuriser votre fiche transporteur, veuillez cliquer
sur le lien suivant :

https://{website}/transporteur/{siret}/confirm/{token}/

Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer ce courriel.
    """.format(
        website=settings.WEBSITE,
        siret=transporteur.siret,
        email=transporteur.email,
        token=token
    )
    send_mail(subject, message, settings.SERVER_EMAIL, [transporteur.email], fail_silently=True)

def mail_managers_changes(transporteur, old_data_changed):
    # Send a mail to managers to track changes
    # The URL is detail view of the front application
    subject = "Modification du transporteur {0}".format(transporteur.siret)
    message = """
Modification du transporteur : {enseigne}
SIRET : {siret}
https://{website}/transporteur/{siret}

Valeurs modifiées :
    """.format(
        enseigne=transporteur.enseigne,
        siret=transporteur.siret,
        website=settings.WEBSITE,
    )

    for field, old_value in old_data_changed.items():
        message += "\n- {field} : {old_value} => {new_value}".format(
            field=field,
            old_value=old_value,
            new_value=getattr(transporteur, field)
        )
    mail_managers(subject, message, fail_silently=True)
