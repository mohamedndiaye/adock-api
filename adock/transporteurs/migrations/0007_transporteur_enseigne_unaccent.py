# Generated by Django 2.0.6 on 2018-07-09 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transporteurs', '0006_unaccent_extension'),
    ]

    operations = [
        migrations.AddField(
            model_name='transporteur',
            name='enseigne_unaccent',
            field=models.CharField(default='', max_length=131),
            preserve_default=False,
        ),
    ]
