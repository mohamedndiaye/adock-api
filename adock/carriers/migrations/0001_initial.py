# Generated by Django 2.1.7 on 2019-04-03 11:23

import adock.carriers.validators
from django.conf import settings
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Carrier",
            fields=[
                (
                    "siret",
                    models.CharField(
                        db_index=True,
                        editable=False,
                        max_length=14,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("raison_sociale", models.CharField(max_length=131)),
                ("enseigne", models.CharField(max_length=131)),
                ("enseigne_unaccent", models.CharField(max_length=131)),
                ("categorie_juridique", models.TextField()),
                ("is_siege", models.BooleanField(default=False)),
                ("adresse", models.CharField(max_length=126)),
                ("code_postal", models.CharField(max_length=5)),
                ("ville", models.CharField(max_length=32)),
                ("departement", models.CharField(blank=True, default="", max_length=3)),
                (
                    "telephone",
                    phonenumber_field.modelfields.PhoneNumberField(
                        blank=True, default="", max_length=128
                    ),
                ),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("date_creation", models.DateField(blank=True, null=True)),
                ("debut_activite", models.DateField(blank=True, null=True)),
                ("code_ape", models.CharField(max_length=5)),
                ("libelle_ape", models.CharField(max_length=65)),
                ("gestionnaire", models.CharField(max_length=131)),
                ("lti_numero", models.CharField(blank=True, default="", max_length=16)),
                ("lti_date_debut", models.DateField(blank=True, null=True)),
                ("lti_date_fin", models.DateField(blank=True, null=True)),
                ("lti_nombre", models.PositiveSmallIntegerField(default=0)),
                ("lc_numero", models.CharField(blank=True, default="", max_length=16)),
                ("lc_date_debut", models.DateField(blank=True, null=True)),
                ("lc_date_fin", models.DateField(blank=True, null=True)),
                ("lc_nombre", models.PositiveSmallIntegerField(default=0)),
                ("numero_tva", models.CharField(blank=True, max_length=13, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("validated_at", models.DateTimeField(blank=True, null=True)),
                ("completeness", models.PositiveSmallIntegerField(default=40)),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Date de la supression de l'établissement du registre des transports.",
                        null=True,
                    ),
                ),
                (
                    "sirene_deleted_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Date de la suppression de l'établissement de la base Sirene.",
                        null=True,
                    ),
                ),
                (
                    "objectif_co2",
                    models.CharField(
                        blank=True,
                        choices=[("ENLISTED", "Engagé"), ("LABELLED", "Labellisé")],
                        default="",
                        max_length=8,
                    ),
                ),
                ("objectif_co2_begin", models.DateField(blank=True, null=True)),
                ("objectif_co2_end", models.DateField(blank=True, null=True)),
                ("longitude", models.FloatField(blank=True, null=True)),
                ("latitude", models.FloatField(blank=True, null=True)),
            ],
            options={"db_table": "carrier"},
        ),
        migrations.CreateModel(
            name="CarrierCertificate",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            (
                                "no-workers",
                                "Attestation de non emploi de travailleurs étrangers",
                            ),
                            (
                                "workers",
                                "Attestation d'emploi de travailleurs étrangers",
                            ),
                        ],
                        max_length=32,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("data", django.contrib.postgres.fields.jsonb.JSONField()),
                (
                    "carrier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="certificates",
                        to="carriers.Carrier",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="carrier_certificates",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "carrier_certificate"},
        ),
        migrations.CreateModel(
            name="CarrierEditable",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "telephone",
                    phonenumber_field.modelfields.PhoneNumberField(max_length=128),
                ),
                ("email", models.EmailField(max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "working_area",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("", "Non définie"),
                            ("INTERNATIONAL", "Internationale"),
                            ("FRANCE", "France"),
                            ("REGION", "Régionale"),
                            ("DEPARTEMENT", "Départementale"),
                        ],
                        default="DEPARTEMENT",
                        max_length=15,
                    ),
                ),
                (
                    "working_area_departements",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=3),
                        blank=True,
                        null=True,
                        size=None,
                        validators=[
                            adock.carriers.validators.validate_french_departement
                        ],
                    ),
                ),
                (
                    "specialities",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            choices=[
                                ("ANIMAL", "Animaux vivants"),
                                ("AUTRE", "Autre"),
                                ("BOIS", "Bois"),
                                ("DECHETS", "Déchets"),
                                ("DEMENAGEMENT", "Déménagement"),
                                ("LOCATION", "Location"),
                                ("LOT", "Lots"),
                                ("MESSAGERIE", "Messagerie express"),
                                ("MULTIMODAL", "Multimodal"),
                                ("PALETTE", "Palettes / Messagerie palettisée"),
                                ("PLATEAU", "Plateau bachés et spécifiques"),
                                ("TEMPERATURE", "Température dirigée"),
                                ("URBAIN", "Urbain / Dernier kilomètre"),
                                ("VEHICULE", "Véhicules"),
                                ("VRAC_LIQUIDE", "Vrac liquide"),
                                ("VRAC_SOLIDE", "Vrac solide"),
                            ],
                            max_length=63,
                        ),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
                ("website", models.URLField(blank=True)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "carrier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="changes",
                        to="carriers.Carrier",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="carrier_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "carrier_editable", "get_latest_by": "pk"},
        ),
        migrations.CreateModel(
            name="CarrierFeed",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("source", models.CharField(max_length=32)),
                ("title", models.CharField(max_length=126)),
                ("url", models.URLField()),
                ("filename", models.FileField(upload_to="")),
                ("downloaded_at", models.DateTimeField(auto_now_add=True)),
                ("applied_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "carrier_feed"},
        ),
        migrations.CreateModel(
            name="CarrierUser",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "carrier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="carriers.Carrier",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "carrier_user"},
        ),
        migrations.AddField(
            model_name="carrier",
            name="editable",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="carriers.CarrierEditable",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="carrieruser", unique_together={("carrier", "user")}
        ),
    ]
