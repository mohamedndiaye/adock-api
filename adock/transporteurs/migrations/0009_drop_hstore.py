# Generated by Django 2.0.4 on 2018-04-09 16:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transporteurs', '0008_auto_20180409_1558'),
    ]

    operations = [
        migrations.RunSQL('DROP EXTENSION IF EXISTS hstore')
    ]