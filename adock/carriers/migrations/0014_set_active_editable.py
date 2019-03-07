# Generated by Django 2.1.7 on 2019-03-05 10:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("carriers", "0013_carrier_editable")]

    operations = [
        migrations.RunSQL(
            """
            update carrier set editable_id = foo.carrier_editable_id
            from (select carrier_id, max(id) as carrier_editable_id
                  from carrier_editable
                  group by carrier_id) foo
            where siret = foo.carrier_id
            """
        )
    ]