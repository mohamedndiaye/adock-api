import smtplib

import sentry_sdk

from django.conf import settings
from django.core.mail import mail_managers, send_mail

from ..core import mails as core_mails
from . import models as carriers_models
from . import tokens as carriers_tokens


def get_recipient_list_from_env(email):
    if settings.ENVIRONMENT == "PREPRODUCTION":
        return (email for (name, email) in settings.MANAGERS)

    return (email,)


def get_message_of_changes(
    changed_fields, current_carrier_editable, new_carrier_editable
):
    message = ""
    for field in changed_fields:
        message += "- {field_label} : {current_value} => {new_value}\n".format(
            field_label=carriers_models.CarrierEditable.INPUT_FIELDS[field],
            current_value=getattr(current_carrier_editable, field),
            new_value=getattr(new_carrier_editable, field),
        )
    return message


def mail_carrier_to_old_email(
    changed_fields, current_carrier_editable, new_carrier_editable
):
    carrier = current_carrier_editable.carrier
    subject = (
        "%sNotification de modification de votre fiche entreprise"
        % settings.EMAIL_SUBJECT_PREFIX
    )
    message = """
Votre fiche entreprise {http_client_url}transporteur/{siret} est en cours de modification avec les changements suivants :

{changes}
Si vous n'êtes pas d'accord avec ces changements, veuillez contacter les responsables du site A Dock.

{signature}
""".format(
        changes=get_message_of_changes(
            changed_fields, current_carrier_editable, new_carrier_editable
        ),
        http_client_url=settings.HTTP_CLIENT_URL,
        siret=carrier.siret,
        signature=core_mails.SIGNATURE,
    )
    recipient_list = get_recipient_list_from_env(current_carrier_editable.email)
    send_mail(
        subject,
        message,
        settings.SERVER_EMAIL,
        recipient_list,
        fail_silently=settings.DEBUG,
    )


def mail_carrier_to_old_email_for_new_user(current_carrier_editable, user):
    carrier = current_carrier_editable.carrier
    user_full_name = user.get_full_name()
    subject = "%sVotre fiche entreprise est associée à l’utilisateur %s" % (
        settings.EMAIL_SUBJECT_PREFIX,
        user.get_full_name(),
    )
    message = """
Bonjour,

Votre entreprise {enseigne} est désormais associée à l’utilisateur {user_full_name}.

Cet utilisateur peut à présent mettre à jour les informations professionnelles présentées sur la fiche de votre entreprise, ainsi que réaliser des démarches administratives pour votre entreprise sur le service A Dock.

{http_client_url}transporteur/{siret}

Pour des raisons de sécurité, toutes modifications ou démarches réalisées par l’utilisateur devront être confirmées via l’adresse e-mail de votre entreprise.

Si c’est une erreur ou que cette personne n’est pas habilitée à faire des modifications pour votre entreprise, signalez-le nous à l’adresse contact@adock.beta.gouv.fr

{signature}
    """.format(
        enseigne=carrier.enseigne,
        http_client_url=settings.HTTP_CLIENT_URL,
        siret=carrier.siret,
        user_full_name=user_full_name,
        signature=core_mails.SIGNATURE,
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
    token = carriers_tokens.carrier_editable_token_generator.make_token(
        new_carrier_editable
    )
    subject = (
        "%sConfirmez la mise à jour de votre fiche entreprise"
        % settings.EMAIL_SUBJECT_PREFIX
    )

    assert new_carrier_editable.created_by
    message = """
Bonjour,

Votre fiche entreprise sur adock.beta.gouv.fr vient d’être mise à jour par {user_full_name}.

Pour confirmer les changements suivants :

{changes}
Cliquez sur le lien :

{http_client_url}transporteur/changement/{new_carrier_editable_id}/confirmer/{token}/

Si c’est une erreur ou que cette personne n’est pas habilitée à faire des modifications pour votre entreprise, signalez-le nous à l’adresse contact@adock.beta.gouv.fr.

En vous remerciant de l’intérêt que vous portez pour A Dock, l’outil de simplification des relations dans le transport de marchandises par route !

{signature}
    """.format(
        changes=get_message_of_changes(
            changed_fields, current_carrier_editable, new_carrier_editable
        ),
        http_client_url=settings.HTTP_CLIENT_URL,
        new_carrier_editable_id=new_carrier_editable.id,
        token=token,
        signature=core_mails.SIGNATURE,
        user_full_name=new_carrier_editable.created_by.get_full_name(),
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
    subject = "log - Modification du transporteur %s" % carrier.siret
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
    subject = "log - La modification du transporteur %s est confirmée." % carrier.siret
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
    token = carriers_tokens.certificate_token_generator.make_token(certificate)
    subject = "%sConfirmez la création de l'attestation" % settings.EMAIL_SUBJECT_PREFIX
    message = """
Bonjour,

Une {certificate_label} vient d’être créée pour votre entreprise sur A Dock par {user_full_name}.

Pour la confirmer, la consulter et la rendre visible sur la fiche de votre entreprise, cliquez sur le lien suivant :

{http_client_url}transporteur/attestation/{certificate_id}/confirmer/{token}/

En vous remerciant de l’intérêt que vous portez pour A Dock, l’outil de simplification des relations dans le transport de marchandises par route !

{signature}
    """.format(
        certificate_id=certificate.id,
        certificate_label=certificate.get_kind_display().lower(),
        http_client_url=settings.HTTP_CLIENT_URL,
        signature=core_mails.SIGNATURE,
        token=token,
        user_full_name=certificate.created_by.get_full_name(),
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
    subject = "log - Nouvelle attestation %s pour le transporteur %s" % (
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
    subject = "log - L'attestation %s du transporteur %s a été confirmée." % (
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


def get_license_message(label, numero, date_fin, new_nombre):
    return "- license {label} n°{numero} expirant le {date_fin} avec {new_nombre} nouvelles copies conformes\n".format(
        label=label, numero=numero, date_fin=date_fin, new_nombre=new_nombre
    )


def mail_carrier_license_renewal_to_confirm(carrier, license_renewal):
    token = carriers_tokens.license_renewal_token_generator.make_token(license_renewal)
    subject = "%sConfirmez la demande de renouvellement de licences pour %s" % (
        settings.EMAIL_SUBJECT_PREFIX,
        carrier.raison_sociale,
    )
    message = """
L'utilisateur {first_name} {last_name} vient d'effectuer la demande de renouvellement de licences suivante :
""".format(
        first_name=license_renewal.created_by.first_name,
        last_name=license_renewal.created_by.last_name,
    )

    if license_renewal.lc_nombre:
        message += get_license_message(
            label="LC",
            numero=carrier.lc_numero,
            date_fin=carrier.lc_date_fin,
            new_nombre=license_renewal.lc_nombre,
        )

    if license_renewal.lti_nombre:
        message += get_license_message(
            label="LTI",
            numero=carrier.lti_numero,
            date_fin=carrier.lti_date_fin,
            new_nombre=license_renewal.lti_nombre,
        )

    message += """
Pour confirmer cette demande, cliquez sur le lien ci-dessous :

{http_client_url}transporteur/renouvellement/{license_renewal_id}/confirmer/{token}/

Elle sera ensuite transmise aux services de la DREAL compétents pour la traiter.

Si c’est une erreur, contactez-nous à l’adresse suivante : contact@adock.beta.gouv.fr

En vous remerciant de l’intérêt que vous portez pour A Dock, l’outil de simplification des relations dans le transport de marchandises par route !

Bien cordialement,

{signature}
    """.format(
        http_client_url=settings.HTTP_CLIENT_URL,
        license_renewal_id=license_renewal.id,
        token=token,
        signature=core_mails.SIGNATURE,
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
    subject = (
        "log - Demande de renouvellement de licence %s pour le transporteur %s"
        % (license_renewal.pk, carrier.siret)
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


def mail_dreal_license_renewal_with_fallback(license_renewal):
    carrier = license_renewal.carrier
    subject = "%sDemande de renouvellement de licences de %s n° SIREN %s" % (
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

    message += """
Merci de bien vouloir instruire cette demande et, le cas échéant, de demander les
pièces justificatives à l’adresse {email}.

{signature}
    """.format(
        email=license_renewal.carrier.editable.email, signature=core_mails.SIGNATURE
    )
    recipient_list = get_recipient_list_from_env(settings.DREAL_EMAIL)
    try:
        send_mail(
            subject,
            message,
            settings.SERVER_EMAIL,
            recipient_list,
            fail_silently=settings.DEBUG,
        )
        return True
    except smtplib.SMTPException as e:
        sentry_sdk.capture_exception(e)
        subject = "log - ÉCHEC - %s" % subject
        mail_managers(subject, message, fail_silently=True)
        return False


def mail_managers_license_renewal_confirmed(license_renewal):
    carrier = license_renewal.carrier
    subject = (
        "log - Demande de renouvellement de licence %s du transporteur %s confirmée"
        % (license_renewal.pk, carrier.siret)
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
