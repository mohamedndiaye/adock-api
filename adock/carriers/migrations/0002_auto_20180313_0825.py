# Generated by Django 2.0.2 on 2018-03-13 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carriers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carrier',
            name='email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AlterField(
            model_name='carrier',
            name='phone',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
