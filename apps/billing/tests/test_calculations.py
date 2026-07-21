"""Regression tests for fiscal calculations (Excel §5.4)."""

from __future__ import annotations

from decimal import Decimal

from django.test import SimpleTestCase

from apps.billing.models import LineType
from apps.billing.services.calculations import calculate_invoice_totals
from apps.core.models import FiscalAppliesTo, FiscalBase, FiscalRule


class ExcelFiscalRegressionTests(SimpleTestCase):
    """Verify service retention totals match the documented Excel example."""

    def test_service_detalle_pago_excel_example(self) -> None:
        # Work backwards: base VES is given; we feed a single service line
        # whose USD*rate equals the Excel base imponible.
        base = Decimal("10821900.10")
        rate = Decimal("1")
        iva_pct = Decimal("0.16")

        rules = [
            FiscalRule(
                code="ret_iva",
                name="Retención IVA",
                percentage=Decimal("0.75"),
                base=FiscalBase.IVA,
                applies_to=FiscalAppliesTo.SERVICE,
                is_active=True,
                sort_order=1,
            ),
            FiscalRule(
                code="islr",
                name="ISLR",
                percentage=Decimal("0.02"),
                base=FiscalBase.BASE_IMPONIBLE,
                applies_to=FiscalAppliesTo.SERVICE,
                is_active=True,
                sort_order=2,
            ),
            FiscalRule(
                code="timbres",
                name="Retención 10x1000",
                percentage=Decimal("0.001"),
                base=FiscalBase.BASE_IMPONIBLE,
                applies_to=FiscalAppliesTo.SERVICE,
                is_active=True,
                sort_order=3,
            ),
            FiscalRule(
                code="fiel",
                name="Fiel cumplimiento",
                percentage=Decimal("0.10"),
                base=FiscalBase.BASE_IMPONIBLE,
                applies_to=FiscalAppliesTo.SERVICE,
                is_active=True,
                sort_order=4,
            ),
            FiscalRule(
                code="laboral",
                name="Retención laboral",
                percentage=Decimal("0.05"),
                base=FiscalBase.BASE_IMPONIBLE,
                applies_to=FiscalAppliesTo.SERVICE,
                is_active=True,
                sort_order=5,
            ),
        ]

        totals = calculate_invoice_totals(
            billable_lines=[
                {
                    "line_type": LineType.SERVICE,
                    "quantity": Decimal("1"),
                    "unit_price_usd": base,
                }
            ],
            exchange_rate=rate,
            iva_pct=iva_pct,
            rules=rules,
        )

        self.assertEqual(totals.base_imponible_ves, Decimal("10821900.10"))
        self.assertEqual(totals.iva_ves, Decimal("1731504.02"))
        self.assertEqual(totals.total_ves, Decimal("12553404.12"))
        # ROUND_HALF_UP: 1731504.02 * 0.75 = 1298628.015 → 1298628.02
        # (Excel captura mostraba 1298628.01; el motor usa HALF_UP consistente)
        self.assertEqual(totals.total_retenciones_ves, Decimal("3149172.94"))
        self.assertEqual(totals.total_a_pagar_ves, Decimal("9404231.18"))
