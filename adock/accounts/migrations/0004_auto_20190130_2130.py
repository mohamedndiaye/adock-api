# Generated by Django 2.1.5 on 2019-01-30 20:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auto_20190122_2133'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='provider',
            field=models.CharField(choices=[('AD', 'A Dock'), ('FC', 'FranceConnect')], default='AD', max_length=2, verbose_name='provider'),
        ),
    ]
