"""Seed default fiscal rules and company settings."""

from __future__ import annotations

from decimal import Decimal

from django.db import migrations


def seed_defaults(apps, schema_editor) -> None:  # type: ignore[no-untyped-def]
    CompanySettings = apps.get_model("core", "CompanySettings")
    FiscalRule = apps.get_model("core", "FiscalRule")

    CompanySettings.objects.get_or_create(
        pk=1,
        defaults={
            "legal_name": "MJ SINO IMPORT, C.A.",
            "rif": "G-20013109-8",
            "fiscal_address": "",
            "iva_pct": Decimal("0.1600"),
        },
    )

    defaults = [
        {
            "code": "ret_iva",
            "name": "Retención IVA",
            "percentage": Decimal("0.750000"),
            "base": "iva",
            "applies_to": "both",
            "sort_order": 10,
        },
        {
            "code": "islr",
            "name": "ISLR",
            "percentage": Decimal("0.020000"),
            "base": "base_imponible",
            "applies_to": "service",
            "sort_order": 20,
        },
        {
            "code": "timbres_10x1000",
            "name": "Retención 10×1000",
            "percentage": Decimal("0.001000"),
            "base": "base_imponible",
            "applies_to": "both",
            "sort_order": 30,
        },
        {
            "code": "resp_social",
            "name": "Responsabilidad social",
            "percentage": Decimal("0.000000"),
            "base": "base_imponible",
            "applies_to": "both",
            "sort_order": 40,
            "is_active": True,
        },
        {
            "code": "fiel_cumplimiento",
            "name": "Retención fiel cumplimiento",
            "percentage": Decimal("0.100000"),
            "base": "base_imponible",
            "applies_to": "both",
            "sort_order": 50,
        },
        {
            "code": "laboral",
            "name": "Retención laboral",
            "percentage": Decimal("0.050000"),
            "base": "base_imponible",
            "applies_to": "both",
            "sort_order": 60,
        },
    ]
    for row in defaults:
        FiscalRule.objects.update_or_create(
            code=row["code"],
            defaults={
                "name": row["name"],
                "percentage": row["percentage"],
                "base": row["base"],
                "applies_to": row["applies_to"],
                "sort_order": row["sort_order"],
                "is_active": row.get("is_active", True),
            },
        )


def unseed(apps, schema_editor) -> None:  # type: ignore[no-untyped-def]
    FiscalRule = apps.get_model("core", "FiscalRule")
    FiscalRule.objects.filter(
        code__in=[
            "ret_iva",
            "islr",
            "timbres_10x1000",
            "resp_social",
            "fiel_cumplimiento",
            "laboral",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_defaults, unseed),
    ]
