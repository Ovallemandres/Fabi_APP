"""Billing calculation engine (IVA, retenciones, totales)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Iterable

from apps.core.models import FiscalAppliesTo, FiscalBase, FiscalRule
from apps.core.services import get_company_settings, list_active_fiscal_rules

from apps.billing.models import LineType, Quote, QuoteLine

TWOPLACES = Decimal("0.01")
ZERO = Decimal("0.00")


def _q(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class QuoteTotals:
    subtotal_usd: Decimal
    iva_usd: Decimal
    total_usd: Decimal
    total_ves_equiv: Decimal
    iva_pct: Decimal


@dataclass(frozen=True)
class GroupTotals:
    line_type: str
    base_imponible: Decimal
    iva: Decimal
    total: Decimal
    retenciones: list[dict[str, Any]]
    total_retenciones: Decimal
    total_a_pagar: Decimal


@dataclass(frozen=True)
class InvoiceTotals:
    base_imponible_ves: Decimal
    iva_ves: Decimal
    total_ves: Decimal
    total_retenciones_ves: Decimal
    total_a_pagar_ves: Decimal
    groups: list[GroupTotals]
    iva_pct: Decimal
    snapshot: dict[str, Any]


def billable_quote_lines(lines: Iterable[QuoteLine]) -> list[QuoteLine]:
    """Lines that charge the client (exclude embedded supplies)."""
    return [
        line
        for line in lines
        if not line.is_embedded and line.line_type != LineType.EMBEDDED_SUPPLY
    ]


def calculate_quote_totals(
    quote: Quote,
    *,
    iva_pct: Decimal | None = None,
) -> QuoteTotals:
    """Subtotal/IVA/total in USD for a quote using company IVA %."""
    pct = iva_pct if iva_pct is not None else get_company_settings().iva_pct
    subtotal = ZERO
    for line in billable_quote_lines(quote.lines.all()):
        subtotal += _q(line.quantity * line.unit_price_usd)
    subtotal = _q(subtotal)
    iva = _q(subtotal * pct)
    total = _q(subtotal + iva)
    equiv = _q(total * quote.exchange_rate)
    return QuoteTotals(
        subtotal_usd=subtotal,
        iva_usd=iva,
        total_usd=total,
        total_ves_equiv=equiv,
        iva_pct=pct,
    )


def _rules_for_group(
    rules: Iterable[FiscalRule],
    group: str,
) -> list[FiscalRule]:
    result: list[FiscalRule] = []
    for rule in rules:
        if rule.applies_to == FiscalAppliesTo.BOTH or rule.applies_to == group:
            result.append(rule)
    return result


def calculate_group_retenciones(
    *,
    base_imponible: Decimal,
    iva: Decimal,
    group: str,
    rules: Iterable[FiscalRule],
) -> tuple[list[dict[str, Any]], Decimal]:
    """Apply active fiscal rules to one line-type group (service or supply)."""
    items: list[dict[str, Any]] = []
    total_ret = ZERO
    for rule in _rules_for_group(rules, group):
        if rule.base == FiscalBase.IVA:
            amount = _q(iva * rule.percentage)
        else:
            amount = _q(base_imponible * rule.percentage)
        items.append(
            {
                "code": rule.code,
                "name": rule.name,
                "percentage": str(rule.percentage),
                "base": rule.base,
                "amount": str(amount),
            }
        )
        total_ret += amount
    return items, _q(total_ret)


def calculate_invoice_totals(
    *,
    billable_lines: Iterable[dict[str, Any]],
    exchange_rate: Decimal,
    iva_pct: Decimal | None = None,
    rules: Iterable[FiscalRule] | None = None,
) -> InvoiceTotals:
    """Compute VES totals + retenciones by group from USD billable line dicts.

    Each line dict needs: line_type (service|supply), quantity, unit_price_usd.
    """
    pct = iva_pct if iva_pct is not None else get_company_settings().iva_pct
    active_rules = list(rules) if rules is not None else list(list_active_fiscal_rules())

    by_group: dict[str, Decimal] = {
        LineType.SERVICE: ZERO,
        LineType.SUPPLY: ZERO,
    }
    for line in billable_lines:
        lt = line["line_type"]
        if lt not in by_group:
            continue
        amount = _q(Decimal(str(line["quantity"])) * Decimal(str(line["unit_price_usd"])) * exchange_rate)
        by_group[lt] += amount

    groups: list[GroupTotals] = []
    base_all = ZERO
    iva_all = ZERO
    total_all = ZERO
    ret_all = ZERO

    for lt, base in by_group.items():
        base = _q(base)
        if base == ZERO and not any(True for _ in _rules_for_group(active_rules, lt)):
            # Still include empty groups only if we want; skip zero groups for snapshot clarity
            if base == ZERO:
                continue
        iva = _q(base * pct)
        total = _q(base + iva)
        ret_items, ret_total = calculate_group_retenciones(
            base_imponible=base,
            iva=iva,
            group=lt,
            rules=active_rules,
        )
        pagar = _q(total - ret_total)
        groups.append(
            GroupTotals(
                line_type=lt,
                base_imponible=base,
                iva=iva,
                total=total,
                retenciones=ret_items,
                total_retenciones=ret_total,
                total_a_pagar=pagar,
            )
        )
        base_all += base
        iva_all += iva
        total_all += total
        ret_all += ret_total

    base_all = _q(base_all)
    iva_all = _q(iva_all)
    total_all = _q(total_all)
    ret_all = _q(ret_all)
    pagar_all = _q(total_all - ret_all)

    snapshot: dict[str, Any] = {
        "iva_pct": str(pct),
        "exchange_rate": str(exchange_rate),
        "groups": [
            {
                "line_type": g.line_type,
                "base_imponible": str(g.base_imponible),
                "iva": str(g.iva),
                "total": str(g.total),
                "retenciones": g.retenciones,
                "total_retenciones": str(g.total_retenciones),
                "total_a_pagar": str(g.total_a_pagar),
            }
            for g in groups
        ],
        "base_imponible_ves": str(base_all),
        "iva_ves": str(iva_all),
        "total_ves": str(total_all),
        "total_retenciones_ves": str(ret_all),
        "total_a_pagar_ves": str(pagar_all),
    }

    return InvoiceTotals(
        base_imponible_ves=base_all,
        iva_ves=iva_all,
        total_ves=total_all,
        total_retenciones_ves=ret_all,
        total_a_pagar_ves=pagar_all,
        groups=groups,
        iva_pct=pct,
        snapshot=snapshot,
    )
