"""Billing views: quotes, invoices, PDF enqueue."""

from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import staff_login_required

from .forms import (
    EmbeddedSupplyFormSet,
    QuoteConvertForm,
    QuoteForm,
    ServiceLineForm,
    SupplyLineForm,
)
from .models import Invoice, InvoiceStatus, Quote, QuoteStatus
from .services.quotes import (
    add_service_line_with_embeds,
    add_supply_line,
    convert_quote_to_invoice,
    create_quote,
    emit_invoice,
    refresh_quote_totals,
    void_invoice,
)
from .tasks import generate_document_pdf


def _is_htmx(request: HttpRequest) -> bool:
    return request.headers.get("HX-Request") == "true"


def _hx_redirect(url: str) -> HttpResponse:
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response


@staff_login_required
def index(request: HttpRequest) -> HttpResponse:
    """Billing hub.

    Context:
        - section: str
    """
    context = {"section": "hub"}
    template = "billing/partials/hub.html" if _is_htmx(request) else "billing/hub.html"
    return render(request, template, context)


@staff_login_required
@require_http_methods(["GET"])
def quote_list(request: HttpRequest) -> HttpResponse:
    """List quotes.

    Context:
        - quotes: QuerySet[Quote]
    """
    quotes = Quote.objects.select_related("truck", "truck__owner").all()
    context = {"quotes": quotes}
    if _is_htmx(request):
        return render(request, "billing/partials/quote_table.html", context)
    return render(request, "billing/quote_list.html", context)


@staff_login_required
@require_http_methods(["GET", "POST"])
def quote_create(request: HttpRequest) -> HttpResponse:
    """Create a quote (numbered on create).

    Context:
        - form: QuoteForm
        - title: str
    """
    form = QuoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        quote = create_quote(
            truck_id=form.cleaned_data["truck"].pk,
            exchange_rate=form.cleaned_data["exchange_rate"],
            notes=form.cleaned_data.get("notes") or "",
        )
        messages.success(request, f"Presupuesto {quote.number} creado.")
        url = reverse("billing:quote_detail", kwargs={"pk": quote.pk})
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "title": "Nuevo presupuesto"}
    template = (
        "billing/partials/quote_form.html"
        if _is_htmx(request)
        else "billing/quote_form.html"
    )
    return render(request, template, context)


@staff_login_required
@require_http_methods(["GET"])
def quote_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Quote detail with lines and actions.

    Context:
        - quote: Quote
        - lines: QuerySet[QuoteLine]
        - convert_form: QuoteConvertForm
        - service_form: ServiceLineForm
        - embed_formset: EmbeddedSupplyFormSet
        - supply_form: SupplyLineForm
    """
    quote = get_object_or_404(
        Quote.objects.select_related("truck", "truck__owner", "truck__driver"),
        pk=pk,
    )
    context = {
        "quote": quote,
        "lines": quote.lines.select_related("service", "supply", "parent_line").all(),
        "convert_form": QuoteConvertForm(),
        "service_form": ServiceLineForm(),
        "embed_formset": EmbeddedSupplyFormSet(prefix="embed"),
        "supply_form": SupplyLineForm(),
    }
    template = (
        "billing/partials/quote_detail.html"
        if _is_htmx(request)
        else "billing/quote_detail.html"
    )
    return render(request, template, context)


@staff_login_required
@require_POST
def quote_add_service_line(request: HttpRequest, pk: int) -> HttpResponse:
    """Add service line + embedded supplies from the same form post."""
    quote = get_object_or_404(Quote, pk=pk)
    if quote.status in {QuoteStatus.FACTURADO, QuoteStatus.ANULADO}:
        messages.error(request, "No se pueden editar líneas en este estado.")
        return redirect("billing:quote_detail", pk=pk)

    form = ServiceLineForm(request.POST)
    formset = EmbeddedSupplyFormSet(request.POST, prefix="embed")
    if form.is_valid() and formset.is_valid():
        embeds = []
        for ef in formset:
            desc = (ef.cleaned_data.get("description") or "").strip()
            supply = ef.cleaned_data.get("supply")
            if not desc and not supply:
                continue
            if supply and not desc:
                desc = supply.name
            embeds.append(
                {
                    "supply_id": supply.pk if supply else None,
                    "description": desc,
                    "quantity": ef.cleaned_data.get("quantity") or Decimal("1"),
                    "cost_usd": ef.cleaned_data.get("cost_usd") or Decimal("0"),
                }
            )
        service = form.cleaned_data.get("service")
        description = form.cleaned_data["description"]
        if service and not description:
            description = service.name
        add_service_line_with_embeds(
            quote,
            service_id=service.pk if service else None,
            description=description,
            quantity=form.cleaned_data["quantity"],
            cost_usd=form.cleaned_data["cost_usd"],
            unit_price_usd=form.cleaned_data["unit_price_usd"],
            embeds=embeds,
        )
        messages.success(request, "Línea de servicio agregada.")
    else:
        messages.error(request, "Revisa los datos de la línea de servicio / embebidos.")
    return redirect("billing:quote_detail", pk=pk)


@staff_login_required
@require_POST
def quote_add_supply_line(request: HttpRequest, pk: int) -> HttpResponse:
    """Add a standalone supply line."""
    quote = get_object_or_404(Quote, pk=pk)
    if quote.status in {QuoteStatus.FACTURADO, QuoteStatus.ANULADO}:
        messages.error(request, "No se pueden editar líneas en este estado.")
        return redirect("billing:quote_detail", pk=pk)

    form = SupplyLineForm(request.POST)
    if form.is_valid():
        supply = form.cleaned_data.get("supply")
        description = form.cleaned_data["description"]
        if supply and not description:
            description = supply.name
        add_supply_line(
            quote,
            supply_id=supply.pk if supply else None,
            description=description,
            quantity=form.cleaned_data["quantity"],
            cost_usd=form.cleaned_data["cost_usd"],
            unit_price_usd=form.cleaned_data["unit_price_usd"],
        )
        messages.success(request, "Línea de suministro agregada.")
    else:
        messages.error(request, "Revisa los datos de la línea de suministro.")
    return redirect("billing:quote_detail", pk=pk)


@staff_login_required
@require_POST
def quote_convert(request: HttpRequest, pk: int) -> HttpResponse:
    """Convert quote to invoice with a new exchange rate."""
    quote = get_object_or_404(Quote, pk=pk)
    form = QuoteConvertForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Debe indicar una tasa de factura válida.")
        return redirect("billing:quote_detail", pk=pk)
    try:
        invoice = convert_quote_to_invoice(
            quote, exchange_rate=form.cleaned_data["exchange_rate"]
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("billing:quote_detail", pk=pk)
    messages.success(request, f"Factura {invoice.number} creada.")
    return redirect("billing:invoice_detail", pk=invoice.pk)


@staff_login_required
@require_http_methods(["GET"])
def invoice_list(request: HttpRequest) -> HttpResponse:
    """List invoices.

    Context:
        - invoices: QuerySet[Invoice]
    """
    invoices = Invoice.objects.select_related("quote", "quote__truck").all()
    context = {"invoices": invoices}
    if _is_htmx(request):
        return render(request, "billing/partials/invoice_table.html", context)
    return render(request, "billing/invoice_list.html", context)


@staff_login_required
@require_http_methods(["GET"])
def invoice_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Invoice detail.

    Context:
        - invoice: Invoice
        - billable_lines: list[InvoiceLine]
        - embedded_lines: list[InvoiceLine] (audit only)
    """
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "quote",
            "quote__truck",
            "quote__truck__owner",
            "quote__truck__driver",
        ),
        pk=pk,
    )
    lines = list(invoice.lines.all())
    context = {
        "invoice": invoice,
        "billable_lines": [ln for ln in lines if ln.is_billable],
        "embedded_lines": [ln for ln in lines if ln.is_embedded],
    }
    template = (
        "billing/partials/invoice_detail.html"
        if _is_htmx(request)
        else "billing/invoice_detail.html"
    )
    return render(request, template, context)


@staff_login_required
@require_POST
def invoice_emit(request: HttpRequest, pk: int) -> HttpResponse:
    """Emit invoice and enqueue PDF."""
    invoice = get_object_or_404(Invoice, pk=pk)
    try:
        emit_invoice(invoice)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("billing:invoice_detail", pk=pk)
    generate_document_pdf.delay("invoice", invoice.pk)
    messages.success(request, "Factura emitida; PDF encolado.")
    response = redirect("billing:invoice_detail", pk=pk)
    if _is_htmx(request):
        r = HttpResponse(status=204)
        r["HX-Redirect"] = reverse("billing:invoice_detail", kwargs={"pk": pk})
        r["HX-Trigger"] = "billingInvoiceEmitted"
        return r
    return response


@staff_login_required
@require_POST
def invoice_void(request: HttpRequest, pk: int) -> HttpResponse:
    """Void invoice and update quote status."""
    invoice = get_object_or_404(Invoice, pk=pk)
    void_invoice(invoice)
    messages.success(request, "Factura anulada.")
    return redirect("billing:invoice_detail", pk=pk)


@staff_login_required
@require_POST
def quote_enqueue_pdf(request: HttpRequest, pk: int) -> HttpResponse:
    """Enqueue quote PDF generation."""
    quote = get_object_or_404(Quote, pk=pk)
    refresh_quote_totals(quote)
    generate_document_pdf.delay("quote", quote.pk)
    messages.success(request, "PDF de presupuesto encolado.")
    if _is_htmx(request):
        r = HttpResponse(status=204)
        r["HX-Redirect"] = reverse("billing:quote_detail", kwargs={"pk": pk})
        r["HX-Trigger"] = "billingQuotePdfQueued"
        return r
    return redirect("billing:quote_detail", pk=pk)
