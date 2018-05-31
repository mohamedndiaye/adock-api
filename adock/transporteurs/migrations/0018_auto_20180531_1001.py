# Generated by Django 2.0.4 on 2018-05-31 10:01

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('transporteurs', '0017_transporteur_in_sirene'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transporteurfeed',
            name='is_applied',
        ),
        migrations.AddField(
            model_name='transporteurfeed',
            name='applied_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transporteurfeed',
            name='downloaded_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
