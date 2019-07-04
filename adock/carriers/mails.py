from django.conf import settings
from django.core.mail import mail_managers, send_mail

from . import tokens


def get_recipient_list_from_env(email):
    if settings.ENVIRONMENT == "PREPRODUCTION":
        return (email for (name, email) in settings.MANAGERS)

    return (email,)


def get_message_of_changes(
    changed_fields, current_carrier_editable, new_carrier_editable
):
    message = ""
    for field in changed_fields:
        message += "- {field} : {current_value} => {new_value}\n".format(
            field=field,
            current_value=getattr(current_carrier_editable, field),
            new_value=getattr(new_carrier_editable, field),
        )
    return message


def mail_carrier_to_old_email(
    changed_fields, current_carrier_editable, new_carrier_editable
):
    carrier = current_carrier_editable.carrier
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
            changed_fields, current_carrier_editable, new_carrier_editable
        ),
    )
    recipient_list = get_recipient_list_from_env(current_carrier_editable.email)
    send_mail(
        subject,
        message,
        settings.SERVER_EMAIL,
        recipient_list,
        fail_silently=settings.DEBUG,
    )


def mail_carrier_editable_to_confirm(
    changed_fields, current_carrier_editable, new_carrier_editable
):
    token = tokens.carrier_editable_token.make_token(new_carrier_editable)
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

{http_client_url}transporteur/changement/{new_carrier_editable_id}/confirmer/{token}/

Cordialement,
L'équipe A Dock
    """.format(
        http_client_url=settings.HTTP_CLIENT_URL,
        new_carrier_editable_id=new_carrier_editable.id,
        token=token,
        changes=get_message_of_changes(
            changed_fields, current_carrier_editable, new_carrier_editable
        ),
    )
    recipient_list = get_recipient_list_from_env(new_carrier_editable.email)
    send_mail(
        subject,
        message,
        settings.SERVER_EMAIL,
        recipient_list,
        fail_silently=settings.DEBUG,
    )


def mail_managers_carrier_changes(
    changed_fields, current_carrier_editable, new_carrier_editable
):
    # Send a mail to managers to track changes
    # The URL is detail view of the front application
    carrier = current_carrier_editable.carrier
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

    message += get_message_of_changes(
        changed_fields, current_carrier_editable, new_carrier_editable
    )
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


def mail_carrier_certificate_to_confirm(carrier, certificate):
    token = tokens.certificate_token.make_token(certificate)
    subject = (
        "%sEn attente de confirmation d'une attestation" % settings.EMAIL_SUBJECT_PREFIX
    )
    message = """
Merci d'avoir créé une attestation sur A Dock, l'application
qui facilite la relation chargeur et transporteur.

Pour la confirmer, cliquez sur ce lien :

{http_client_url}transporteur/attestation/{certificate_id}/confirmer/{token}/

Cordialement,
L'équipe A Dock
    """.format(
        http_client_url=settings.HTTP_CLIENT_URL,
        certificate_id=certificate.id,
        token=token,
    )
    recipient_list = get_recipient_list_from_env(carrier.editable.email)
    send_mail(
        subject,
        message,
        settings.SERVER_EMAIL,
        recipient_list,
        fail_silently=settings.DEBUG,
    )


def mail_managers_new_certificate(certificate):
    carrier = certificate.carrier
    subject = "Nouvelle attestation %s pour le transporteur %s" % (
        certificate.pk,
        carrier.siret,
    )
    message = """
Transporteur : {enseigne}
Type d'attestation : {kind}
Utilisateur : {user}
Données :
{data}

{http_client_url}transporteur/{siret}
""".format(
        data=certificate.data,
        enseigne=carrier.enseigne,
        http_client_url=settings.HTTP_CLIENT_URL,
        kind=certificate.get_kind_display(),
        siret=carrier.siret,
        user=certificate.created_by,
    )
    mail_managers(subject, message, fail_silently=True)


def mail_managers_certificate_confirmed(certificate):
    carrier = certificate.carrier
    subject = "L'attestation %s du transporteur %s a été confirmée." % (
        certificate.pk,
        carrier.siret,
    )
    message = """
Transporteur : {enseigne}
Type d'attestation : {kind}
Utilisateur : {user}
Données :
{data}

{http_client_url}transporteur/{siret}
    """.format(
        data=certificate.data,
        enseigne=carrier.enseigne,
        http_client_url=settings.HTTP_CLIENT_URL,
        kind=certificate.get_kind_display(),
        siret=carrier.siret,
        user=certificate.created_by,
    )
    mail_managers(subject, message, fail_silently=True)


def mail_carrier_license_renewal_to_confirm(carrier, license_renewal):
    token = tokens.license_renewal_token.make_token(license_renewal)
    subject = (
        "%sEn attente de confirmation d'une demande de renouvellement de license"
        % settings.EMAIL_SUBJECT_PREFIX
    )
    message = """
Merci d'avoir effectué une demande de renouvellement de license sur A Dock,
l'application qui facilite la relation chargeur et transporteur.

Pour la confirmer, cliquez sur ce lien :

{http_client_url}transporteur/renouvellement/{license_renewal_id}/confirmer/{token}/

Cordialement,
L'équipe A Dock
    """.format(
        http_client_url=settings.HTTP_CLIENT_URL,
        license_renewal_id=license_renewal.id,
        token=token,
    )
    recipient_list = get_recipient_list_from_env(carrier.editable.email)
    send_mail(
        subject,
        message,
        settings.SERVER_EMAIL,
        recipient_list,
        fail_silently=settings.DEBUG,
    )


def mail_managers_new_license_renewal(license_renewal):
    carrier = license_renewal.carrier
    subject = "Demande de renouvellement de licence %s pour le transporteur %s" % (
        license_renewal.pk,
        carrier.siret,
    )
    message = """
Transporteur : {enseigne}
Utilisateur : {user}
Nombre de LTI : {lti_nombre}
Nombre de LC : {lc_nombre}

{http_client_url}transporteur/{siret}
""".format(
        enseigne=carrier.enseigne,
        user=license_renewal.created_by,
        lti_nombre=license_renewal.lti_nombre,
        lc_nombre=license_renewal.lc_nombre,
        http_client_url=settings.HTTP_CLIENT_URL,
        siret=carrier.siret,
    )
    mail_managers(subject, message, fail_silently=True)


def get_license_message(label, numero, date_fin, new_nombre):
    return "- license {label} n°{numero} expirant le {date_fin} avec {new_nombre} de copies conformes\n".format(
        label=label, numero=numero, date_fin=date_fin, new_nombre=new_nombre
    )


def mail_dreal_license_renewal(license_renewal):
    carrier = license_renewal.carrier
    subject = "%sDemande de renouvellement de licence de %s n° SIREN %s" % (
        settings.EMAIL_SUBJECT_PREFIX,
        carrier.raison_sociale,
        carrier.get_siren(),
    )

    message = """
Bonjour DREAL Bretagne,

L'entreprise {raison_sociale} n° SIREN {siren} a fait, par l'intermédiaire de
{first_name} {last_name} une demande de renouvellement de :
""".format(
        raison_sociale=carrier.raison_sociale,
        siren=carrier.get_siren(),
        first_name=license_renewal.created_by.first_name,
        last_name=license_renewal.created_by.last_name,
    )
    if license_renewal.lti_nombre:
        message += get_license_message(
            label="LTI",
            numero=carrier.lti_numero,
            date_fin=carrier.lti_date_fin,
            new_nombre=license_renewal.lti_nombre,
        )

    if license_renewal.lc_nombre:
        message += get_license_message(
            label="LC",
            numero=carrier.lc_numero,
            date_fin=carrier.lc_date_fin,
            new_nombre=license_renewal.lc_nombre,
        )

    message += (
        """
Merci de bien vouloir instruire cette demande et, le cas échéant, de demander les
pièces justificatives à l’adresse %s.
Cordialement,

L’équipe A Dock"""
        % license_renewal.carrier.editable.email
    )
    recipient_list = get_recipient_list_from_env(settings.DREAL_EMAIL)
    send_mail(
        subject,
        message,
        settings.SERVER_EMAIL,
        recipient_list,
        fail_silently=settings.DEBUG,
    )


def mail_managers_license_renewal_confirmed(license_renewal):
    carrier = license_renewal.carrier
    subject = "Demande de renouvellement de licence %s du transporteur %s confirmée" % (
        license_renewal.pk,
        carrier.siret,
    )
    message = """
Transporteur : {enseigne}
Utilisateur : {user}
Nombre de LTI : {lti_nombre}
Nombre de LC : {lc_nombre}

{http_client_url}transporteur/{siret}
    """.format(
        enseigne=carrier.enseigne,
        user=license_renewal.created_by,
        lti_nombre=license_renewal.lti_nombre,
        lc_nombre=license_renewal.lc_nombre,
        http_client_url=settings.HTTP_CLIENT_URL,
        siret=carrier.siret,
    )
    mail_managers(subject, message, fail_silently=True)
