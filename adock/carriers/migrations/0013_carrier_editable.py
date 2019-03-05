# Generated by Django 2.1.7 on 2019-03-05 09:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('carriers', '0012_create_editables_from_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='carrier',
            name='editable',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='carriers.CarrierEditable'),
        ),
    ]
