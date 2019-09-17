# Generated by Django 2.2.3 on 2019-09-16 08:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("carriers", "0014_auto_20190910_1522")]

    operations = [
        migrations.RunSQL(
            """
            insert into carrier_user(carrier_id, user_id, created_at)
                select carrier_id, created_by_id, min(created_at) as created_at
                from carrier_editable
                where created_by_id is not null and
                    confirmed_at is not null
                group by carrier_id, created_by_id
            """
        )
    ]