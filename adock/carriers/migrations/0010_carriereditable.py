# Generated by Django 2.1.7 on 2019-03-05 08:43

import adock.carriers.validators
from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("carriers", "0009_auto_20190211_0759"),
    ]

    operations = [
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
                    phonenumber_field.modelfields.PhoneNumberField(
                        blank=True, default="", max_length=128
                    ),
                ),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("validated_at", models.DateTimeField(blank=True, null=True)),
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
                        default="",
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
            options={"db_table": "carrier_editable"},
        )
    ]
