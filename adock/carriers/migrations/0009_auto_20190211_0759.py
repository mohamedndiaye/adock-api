# Generated by Django 2.1.5 on 2019-02-11 06:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("carriers", "0008_auto_20190131_2227")]

    operations = [
        migrations.RemoveField(model_name="carrier", name="edit_code"),
        migrations.RemoveField(model_name="carrier", name="edit_code_at"),
    ]
