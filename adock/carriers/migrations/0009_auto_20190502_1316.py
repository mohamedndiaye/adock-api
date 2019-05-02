# Generated by Django 2.2.1 on 2019-05-02 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carriers', '0008_remove_old_trgm_enseigne_unaccent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carriercertificate',
            name='kind',
            field=models.CharField(choices=[('NO_WORKERS', 'Attestation de non emploi de travailleurs étrangers'), ('WORKERS', "Attestation d'emploi de travailleurs étrangers")], max_length=32),
        ),
    ]
