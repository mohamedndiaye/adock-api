# Generated by Django 2.0.2 on 2018-03-13 14:37

import adock.transporteurs.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transporteurs', '0002_auto_20180313_1423'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transporteur',
            name='nic',
        ),
        migrations.RemoveField(
            model_name='transporteur',
            name='siren',
        ),
        migrations.AlterField(
            model_name='transporteur',
            name='siret',
            field=models.CharField(db_index=True, editable=False, max_length=14, unique=True, validators=[adock.transporteurs.validators.validate_siret]),
        ),
    ]