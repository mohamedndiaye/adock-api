# Generated by Django 2.0.6 on 2018-07-10 12:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transporteurs', '0010_drop_index_search_trgm_enseigne'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='transporteur',
            name='transporteur_search_order_by',
        ),
    ]
