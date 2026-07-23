# Generated manually — backfill quote IVA + fiscal rule snapshots

from decimal import Decimal

from django.db import migrations


def backfill_quote_fiscal(apps, schema_editor):
    Quote = apps.get_model("billing", "Quote")
    QuoteFiscalRule = apps.get_model("billing", "QuoteFiscalRule")
    FiscalRule = apps.get_model("core", "FiscalRule")
    CompanySettings = apps.get_model("core", "CompanySettings")

    company = CompanySettings.objects.filter(pk=1).first()
    iva_pct = company.iva_pct if company else Decimal("0.1600")
    Quote.objects.all().update(iva_pct=iva_pct)

    templates = list(
        FiscalRule.objects.filter(is_active=True).order_by("sort_order", "code")
    )
    for quote in Quote.objects.all().iterator():
        if QuoteFiscalRule.objects.filter(quote_id=quote.pk).exists():
            continue
        QuoteFiscalRule.objects.bulk_create(
            [
                QuoteFiscalRule(
                    quote_id=quote.pk,
                    code=rule.code,
                    name=rule.name,
                    percentage=rule.percentage,
                    base=rule.base,
                    applies_to=rule.applies_to,
                    is_active=rule.is_active,
                    sort_order=rule.sort_order,
                )
                for rule in templates
            ]
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0003_quote_fiscal_rules_and_price_freshness"),
        ("core", "0002_seed_fiscal_defaults"),
    ]

    operations = [
        migrations.RunPython(backfill_quote_fiscal, noop_reverse),
    ]
