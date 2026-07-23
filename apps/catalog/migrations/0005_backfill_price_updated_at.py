# Generated manually — backfill price_updated_at from updated_at

from django.db import migrations
from django.utils import timezone


def backfill_price_dates(apps, schema_editor):
    now = timezone.now()
    Service = apps.get_model("catalog", "Service")
    Supply = apps.get_model("catalog", "Supply")
    for Model in (Service, Supply):
        for row in Model.objects.filter(price_updated_at__isnull=True).iterator():
            Model.objects.filter(pk=row.pk).update(
                price_updated_at=getattr(row, "updated_at", None) or now
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0004_quote_fiscal_rules_and_price_freshness"),
    ]

    operations = [
        migrations.RunPython(backfill_price_dates, noop_reverse),
    ]
