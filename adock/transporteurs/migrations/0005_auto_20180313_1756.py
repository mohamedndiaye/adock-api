# Generated by Django 2.0.2 on 2018-03-13 17:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transporteurs', '0004_auto_20180313_1447'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transporteur',
            old_name='greater_than_35t_licenses',
            new_name='greater_than_3_5_licenses',
        ),
        migrations.RenameField(
            model_name='transporteur',
            old_name='lower_than_35t_licenses',
            new_name='lower_than_3_5_licenses',
        ),
    ]