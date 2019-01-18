# Generated by Django 2.1.5 on 2019-01-18 14:05

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carriers', '0006_carriercertificate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carrier',
            name='specialities',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('ANIMAL', 'Animaux vivants'), ('AUTRE', 'Autre'), ('BOIS', 'Bois'), ('DECHETS', 'Déchets'), ('DEMENAGEMENT', 'Déménagement'), ('LOCATION', 'Location'), ('LOT', 'Lots'), ('MESSAGERIE', 'Messagerie express'), ('MULTIMODAL', 'Multimodal'), ('PALETTE', 'Palettes / Messagerie palettisée'), ('PLATEAU', 'Plateau bachés et spécifiques'), ('TEMPERATURE', 'Température dirigée'), ('URBAIN', 'Urbain / Dernier kilomètre'), ('VEHICULE', 'Véhicules'), ('VRAC_LIQUIDE', 'Vrac liquide'), ('VRAC_SOLIDE', 'Vrac solide')], max_length=63), blank=True, null=True, size=None),
        ),
    ]