"""Quote/invoice lifecycle services (create, recalc, convert, void)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction

from apps.core.models import DocumentKind
from apps.core.services import allocate_document_number

from apps.billing.models import (
    Invoice,
    InvoiceLine,
    InvoiceStatus,
    LineType,
    Quote,
    QuoteKind,
    QuoteLine,
    QuoteStatus,
)
from apps.billing.services.calculations import calculate_invoice_totals, calculate_quote_totals


@transaction.atomic
def create_quote(
    *,
    truck_id: int,
    exchange_rate: Decimal,
    quote_kind: str,
    notes: str = "",
) -> Quote:
    """Create a numbered quote in borrador status for services or supplies."""
    if quote_kind not in {QuoteKind.SERVICES, QuoteKind.SUPPLIES}:
        raise ValueError("Tipo de presupuesto inválido.")
    number = allocate_document_number(DocumentKind.QUOTE)
    return Quote.objects.create(
        number=number,
        truck_id=truck_id,
        quote_kind=quote_kind,
        exchange_rate=exchange_rate,
        notes=notes,
        status=QuoteStatus.BORRADOR,
    )


def refresh_quote_totals(quote: Quote) -> Quote:
    """Recalculate and persist USD totals on the quote."""
    totals = calculate_quote_totals(quote)
    quote.subtotal_usd = totals.subtotal_usd
    quote.iva_usd = totals.iva_usd
    quote.total_usd = totals.total_usd
    quote.save(update_fields=["subtotal_usd", "iva_usd", "total_usd", "updated_at"])
    return quote


@transaction.atomic
def create_quote_with_lines(
    *,
    truck_id: int,
    exchange_rate: Decimal,
    quote_kind: str,
    lines: list[dict[str, Any]],
    notes: str = "",
) -> Quote:
    """Create quote and all billable lines in one step (wizard).

    For ``services`` lines: service_id, description, quantity, cost_usd, unit_price_usd,
    optional embeds list.
    For ``supplies`` lines: supply_id, description, quantity, cost_usd, unit_price_usd.
    """
    if not lines:
        raise ValueError("Debe agregar al menos un ítem al presupuesto.")

    quote = create_quote(
        truck_id=truck_id,
        exchange_rate=exchange_rate,
        quote_kind=quote_kind,
        notes=notes,
    )

    if quote_kind == QuoteKind.SERVICES:
        for raw in lines:
            add_service_line_with_embeds(
                quote,
                service_id=raw.get("service_id"),
                description=raw["description"],
                quantity=Decimal(str(raw["quantity"])),
                cost_usd=Decimal(str(raw["cost_usd"])),
                unit_price_usd=Decimal(str(raw["unit_price_usd"])),
                embeds=raw.get("embeds") or [],
            )
    else:
        for raw in lines:
            add_supply_line(
                quote,
                supply_id=raw.get("supply_id"),
                description=raw["description"],
                quantity=Decimal(str(raw["quantity"])),
                cost_usd=Decimal(str(raw["cost_usd"])),
                unit_price_usd=Decimal(str(raw["unit_price_usd"])),
            )

    return refresh_quote_totals(quote)


@transaction.atomic
def add_service_line_with_embeds(
    quote: Quote,
    *,
    service_id: int | None,
    description: str,
    quantity: Decimal,
    cost_usd: Decimal,
    unit_price_usd: Decimal,
    embeds: list[dict[str, Any]],
) -> QuoteLine:
    """Add a service line and optional embedded supplies in one transaction."""
    if quote.quote_kind != QuoteKind.SERVICES:
        raise ValueError("Este presupuesto es solo de suministros.")
    parent = QuoteLine.objects.create(
        quote=quote,
        line_type=LineType.SERVICE,
        service_id=service_id,
        description=description,
        quantity=quantity,
        cost_usd=cost_usd,
        unit_price_usd=unit_price_usd,
        is_embedded=False,
        sort_order=quote.lines.count(),
    )
    for idx, emb in enumerate(embeds):
        QuoteLine.objects.create(
            quote=quote,
            line_type=LineType.EMBEDDED_SUPPLY,
            supply_id=emb.get("supply_id"),
            description=emb["description"],
            quantity=Decimal(str(emb.get("quantity", "1"))),
            cost_usd=Decimal(str(emb.get("cost_usd", "0"))),
            unit_price_usd=Decimal("0.00"),
            is_embedded=True,
            parent_line=parent,
            sort_order=parent.sort_order + idx + 1,
        )
    refresh_quote_totals(quote)
    return parent


@transaction.atomic
def add_supply_line(
    quote: Quote,
    *,
    supply_id: int | None,
    description: str,
    quantity: Decimal,
    cost_usd: Decimal,
    unit_price_usd: Decimal,
) -> QuoteLine:
    """Add a standalone supply line (billable)."""
    if quote.quote_kind != QuoteKind.SUPPLIES:
        raise ValueError("Este presupuesto es solo de servicios.")
    line = QuoteLine.objects.create(
        quote=quote,
        line_type=LineType.SUPPLY,
        supply_id=supply_id,
        description=description,
        quantity=quantity,
        cost_usd=cost_usd,
        unit_price_usd=unit_price_usd,
        is_embedded=False,
        sort_order=quote.lines.count(),
    )
    refresh_quote_totals(quote)
    return line


@transaction.atomic
def mark_quote_enviado(quote: Quote) -> Quote:
    """Mark quote as sent to client."""
    if quote.status not in {QuoteStatus.BORRADOR, QuoteStatus.CONFIRMAR_PRESUPUESTO_FACTURA_ANULADA}:
        raise ValueError("Solo se puede enviar un presupuesto en borrador o pendiente de confirmación.")
    if not quote.lines.filter(is_embedded=False).exists():
        raise ValueError("El presupuesto no tiene líneas facturables.")
    quote.status = QuoteStatus.ENVIADO
    quote.save(update_fields=["status", "updated_at"])
    return quote


@transaction.atomic
def mark_quote_aceptado(quote: Quote) -> Quote:
    """Mark quote as accepted by client (ready to invoice)."""
    if quote.status not in {
        QuoteStatus.ENVIADO,
        QuoteStatus.BORRADOR,
        QuoteStatus.CONFIRMAR_PRESUPUESTO_FACTURA_ANULADA,
    }:
        raise ValueError("No se puede aceptar este presupuesto en su estado actual.")
    quote.status = QuoteStatus.ACEPTADO
    quote.save(update_fields=["status", "updated_at"])
    return quote


@transaction.atomic
def convert_quote_to_invoice(quote: Quote, *, exchange_rate: Decimal) -> Invoice:
    """Create invoice from quote (1:1), recalc VES with new BCV rate, mark quote facturado."""
    if hasattr(quote, "invoice"):
        raise ValueError("Este presupuesto ya tiene factura asociada.")
    if quote.status == QuoteStatus.ANULADO:
        raise ValueError("No se puede facturar un presupuesto anulado.")
    if quote.status == QuoteStatus.FACTURADO:
        raise ValueError("El presupuesto ya está facturado.")
    if quote.status not in {
        QuoteStatus.ACEPTADO,
        QuoteStatus.ENVIADO,
        QuoteStatus.BORRADOR,
        QuoteStatus.CONFIRMAR_PRESUPUESTO_FACTURA_ANULADA,
    }:
        raise ValueError("Estado de presupuesto no válido para facturar.")

    number = allocate_document_number(DocumentKind.INVOICE)
    billable = [
        {
            "line_type": line.line_type,
            "quantity": line.quantity,
            "unit_price_usd": line.unit_price_usd,
        }
        for line in quote.lines.filter(is_embedded=False).exclude(
            line_type=LineType.EMBEDDED_SUPPLY
        )
    ]
    totals = calculate_invoice_totals(
        billable_lines=billable,
        exchange_rate=exchange_rate,
    )

    invoice = Invoice.objects.create(
        number=number,
        quote=quote,
        status=InvoiceStatus.BORRADOR,
        exchange_rate=exchange_rate,
        base_imponible_ves=totals.base_imponible_ves,
        iva_ves=totals.iva_ves,
        total_ves=totals.total_ves,
        total_retenciones_ves=totals.total_retenciones_ves,
        total_a_pagar_ves=totals.total_a_pagar_ves,
        calculation_snapshot=totals.snapshot,
    )

    sort = 0
    for line in quote.lines.all().order_by("sort_order", "pk"):
        is_billable = not line.is_embedded and line.line_type != LineType.EMBEDDED_SUPPLY
        unit_ves = (line.unit_price_usd * exchange_rate).quantize(Decimal("0.01"))
        line_total = (
            (line.quantity * line.unit_price_usd * exchange_rate).quantize(Decimal("0.01"))
            if is_billable
            else Decimal("0.00")
        )
        InvoiceLine.objects.create(
            invoice=invoice,
            line_type=line.line_type,
            description=line.description,
            quantity=line.quantity,
            unit_price_usd=line.unit_price_usd,
            cost_usd=line.cost_usd,
            unit_price_ves=unit_ves if is_billable else Decimal("0.00"),
            line_total_ves=line_total,
            is_embedded=line.is_embedded or line.line_type == LineType.EMBEDDED_SUPPLY,
            is_billable=is_billable,
            sort_order=sort,
        )
        sort += 1

    quote.status = QuoteStatus.FACTURADO
    quote.save(update_fields=["status", "updated_at"])
    return invoice


@transaction.atomic
def emit_invoice(invoice: Invoice) -> Invoice:
    """Mark invoice as emitida (locked for amount edits)."""
    if invoice.status == InvoiceStatus.ANULADA:
        raise ValueError("No se puede emitir una factura anulada.")
    invoice.status = InvoiceStatus.EMITIDA
    invoice.save(update_fields=["status", "updated_at"])
    return invoice


@transaction.atomic
def void_invoice(invoice: Invoice) -> Invoice:
    """Anular factura and move quote to confirmar_presupuesto_factura_anulada."""
    invoice.status = InvoiceStatus.ANULADA
    invoice.save(update_fields=["status", "updated_at"])
    quote = invoice.quote
    quote.status = QuoteStatus.CONFIRMAR_PRESUPUESTO_FACTURA_ANULADA
    quote.save(update_fields=["status", "updated_at"])
    return invoice
