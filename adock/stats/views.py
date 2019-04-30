from django.db import connection
from django.http import JsonResponse

from adock.carriers import models as carriers_models
from adock.meta import models as meta_models


def stats(request):
    # Counters (total)
    modified_carriers = carriers_models.Carrier.objects.filter(
        editable__confirmed_at__isnull=False
    ).count()
    certificates = carriers_models.CarrierCertificate.objects.filter(
        confirmed_at__isnull=False
    ).count()
    try:
        nginx_stats = meta_models.Meta.objects.get(name="nginx")
    except meta_models.Meta.DoesNotExist:
        nginx_stats = None

    modified_carriers_per_month = []
    with connection.cursor() as cursor:
        # Collect the number of validated sheets by month for the last 6 months
        # A bit slow, 18ms...
        cursor.execute(
            """
            SELECT
                gs.generated_month::date,
                count(carrier.siret)
            FROM
               (SELECT date_trunc('month', calendar.date) as generated_month
                FROM generate_series(
                        now() - interval '5 month',
                        now(),
                        interval '1 month') AS calendar(date)
                ) gs
            LEFT JOIN carrier_editable ce
                   ON ce.confirmed_at is not null AND
                      date_trunc('month', ce.confirmed_at) = generated_month
            LEFT JOIN carrier
                   ON carrier.editable_id = ce.id
            GROUP BY generated_month
            ORDER BY generated_month"""
        )
        for row in cursor.fetchall():
            modified_carriers_per_month.append({"month": row[0], "count": row[1]})

    data = {
        # Total
        "certificates": certificates,
        "modified_carriers": modified_carriers,
        # Only for the recent period (6 months)
        "modified_carriers_per_month": modified_carriers_per_month,
    }

    if nginx_stats:
        data["carrier_views"] = nginx_stats.data["carriers"]
        data["certificate_views"] = nginx_stats.data["certificates"]
        data["search_views"] = nginx_stats.data["searches"]

    return JsonResponse(data)
