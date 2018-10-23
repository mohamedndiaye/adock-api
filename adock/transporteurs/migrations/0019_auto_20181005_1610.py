# Generated by Django 2.1.2 on 2018-10-05 14:10

import phonenumber_field.modelfields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("transporteurs", "0018_auto_20180927_1150")]

    operations = [
        migrations.AlterField(
            model_name="transporteur",
            name="telephone",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True, default="", max_length=128
            ),
        )
    ]
