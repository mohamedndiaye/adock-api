# Generated by Django 2.1 on 2018-09-13 20:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transporteurs', '0015_auto_20180820_1242'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transporteurfeed',
            name='filename',
            field=models.FileField(upload_to=''),
        ),
    ]