# Generated by Django 2.2.2 on 2019-07-03 17:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("carriers", "0011_carrierlicenserenewal")]

    operations = [
        migrations.RunSQL(
            "update carrier set enseigne_unaccent = translate(enseigne_unaccent, ',.', '')"
        )
    ]
