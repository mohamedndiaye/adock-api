# Generated by Django 2.1.7 on 2019-04-03 17:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("carriers", "0004_index_enseigne_unaccent")]

    operations = [migrations.RemoveField(model_name="carrier", name="validated_at")]
