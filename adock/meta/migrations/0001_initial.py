# Generated by Django 2.0.4 on 2018-04-09 11:11

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Meta",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=63, unique=True)),
                ("data", django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            options={"db_table": "meta"},
        )
    ]
