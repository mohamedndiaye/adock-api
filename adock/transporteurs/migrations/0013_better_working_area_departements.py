# Generated by Django 2.1 on 2018-08-13 10:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transporteurs', '0012_auto_20180809_1514'),
    ]

    operations = [
        migrations.RunSQL("""
            update transporteur
               set working_area_departements = array[departement]
               where validated_at is not null;
        """)
    ]
