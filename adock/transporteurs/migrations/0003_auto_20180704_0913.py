# Generated by Django 2.0.6 on 2018-07-04 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transporteurs', '0002_transporteur_email_confirmed_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='transporteur',
            name='edit_code',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transporteur',
            name='edit_code_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]