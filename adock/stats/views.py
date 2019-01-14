from django.db import connection
from django.http import JsonResponse

from adock.accounts.decorators import user_is_staff
from adock.carriers import models as carriers_models

# Create your views here.
@user_is_staff()
def stats(request):
    # Counters (total)
    validated_carriers = carriers_models.Carrier.objects.filter(
        validated_at__isnull=False
    ).count()
    locked_carriers = carriers_models.Carrier.objects.filter(
        email_confirmed_at__isnull=False
    ).count()

    validated_carriers_per_month = []
    with connection.cursor() as cursor:
        # Collect the number of validated sheets by month for the last 6 months
        # A bit slow, 18ms...
        cursor.execute(
            """
            SELECT
                gs.generated_month::date,
                count(t.siret)
            FROM
                (SELECT date_trunc('month', calendar.date) as generated_month
                FROM generate_series(
                        now() - interval '5 month',
                        now(),
                        interval '1 month') AS calendar(date)) gs
                LEFT JOIN carrier t
                    ON t.validated_at is not null AND
                        date_trunc('month', t.validated_at) = generated_month
            GROUP BY generated_month
            ORDER BY generated_month"""
        )
        for row in cursor.fetchall():
            validated_carriers_per_month.append({"month": row[0], "count": row[1]})

    return JsonResponse(
        {
            # Total
            "validated_carriers": validated_carriers,
            "locked_carriers": locked_carriers,
            # Only for the recent period (6 months)
            "validated_carriers_per_month": validated_carriers_per_month,
        }
    )
