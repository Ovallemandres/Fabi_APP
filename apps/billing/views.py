"""Billing views: quotes, invoices, PDF enqueue."""

from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.catalog.models import Service, Supply
from apps.catalog.services import price_freshness
from apps.core.decorators import staff_login_required
from apps.fleet.models import Truck

from .forms import (
    QuoteConvertForm,
    QuoteFiscalRuleEditForm,
    QuoteIvaForm,
    QuoteWizardMetaForm,
    WizardServiceFormSet,
    WizardSupplyFormSet,
)
from .models import Invoice, InvoiceStatus, Quote, QuoteFiscalRule, QuoteKind, QuoteStatus
from .services.pdf import run_generate_document_pdf
from .services.quotes import (
    convert_quote_to_invoice,
    copy_fiscal_rules_to_quote,
    create_quote_with_lines,
    emit_invoice,
    mark_quote_aceptado,
    mark_quote_enviado,
    refresh_quote_totals,
    void_invoice,
)


def _is_htmx(request: HttpRequest) -> bool:
    return request.headers.get("HX-Request") == "true"


def _hx_redirect(url: str) -> HttpResponse:
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response


@staff_login_required
def index(request: HttpRequest) -> HttpResponse:
    """Billing hub with quote/invoice history entry points by status.

    Context:
        - section: str
        - quotes_*_url / invoices_*_url: str
        - quotes_*_meta / invoices_*_meta: str
    """
    quotes = Quote.objects.all()
    invoices = Invoice.objects.all()
    active_statuses = [
        QuoteStatus.BORRADOR,
        QuoteStatus.ENVIADO,
        QuoteStatus.CONFIRMAR_PRESUPUESTO_FACTURA_ANULADA,
    ]
    context = {
        "section": "hub",
        "quotes_all_url": reverse("billing:quote_list"),
        "quotes_active_url": reverse("billing:quote_list") + "?status=active",
        "quotes_accepted_url": reverse("billing:quote_list") + "?status=aceptado",
        "quotes_invoiced_url": reverse("billing:quote_list") + "?status=facturado",
        "quotes_void_url": reverse("billing:quote_list") + "?status=anulado",
        "quotes_all_meta": f"{quotes.count()} en total",
        "quotes_active_meta": f"{quotes.filter(status__in=active_statuses).count()} activos",
        "quotes_accepted_meta": f"{quotes.filter(status=QuoteStatus.ACEPTADO).count()} aceptados",
        "quotes_invoiced_meta": f"{quotes.filter(status=QuoteStatus.FACTURADO).count()} facturados",
        "quotes_void_meta": f"{quotes.filter(status=QuoteStatus.ANULADO).count()} anulados",
        "invoices_all_url": reverse("billing:invoice_list"),
        "invoices_draft_url": reverse("billing:invoice_list") + "?status=borrador",
        "invoices_issued_url": reverse("billing:invoice_list") + "?status=emitida",
        "invoices_void_url": reverse("billing:invoice_list") + "?status=anulada",
        "invoices_all_meta": f"{invoices.count()} en total",
        "invoices_draft_meta": f"{invoices.filter(status=InvoiceStatus.BORRADOR).count()} borrador",
        "invoices_issued_meta": f"{invoices.filter(status=InvoiceStatus.EMITIDA).count()} emitidas",
        "invoices_void_meta": f"{invoices.filter(status=InvoiceStatus.ANULADA).count()} anuladas",
    }
    template = "billing/partials/hub.html" if _is_htmx(request) else "billing/hub.html"
    return render(request, template, context)


@staff_login_required
@require_http_methods(["GET"])
def quote_list(request: HttpRequest) -> HttpResponse:
    """List quotes with optional status filter (histórico).

    Context:
        - quotes: QuerySet[Quote]
        - status_filter: str
        - status_label: str
    """
    status_filter = request.GET.get("status", "").strip()
    quotes = Quote.objects.select_related("truck", "truck__owner").all()
    status_label = "Todos"
    if status_filter == "active":
        quotes = quotes.filter(
            status__in=[
                QuoteStatus.BORRADOR,
                QuoteStatus.ENVIADO,
                QuoteStatus.CONFIRMAR_PRESUPUESTO_FACTURA_ANULADA,
            ]
        )
        status_label = "Activos / en proceso"
    elif status_filter in {c.value for c in QuoteStatus}:
        quotes = quotes.filter(status=status_filter)
        status_label = dict(QuoteStatus.choices).get(status_filter, status_filter)
    context = {
        "quotes": quotes,
        "status_filter": status_filter,
        "status_label": status_label,
    }
    if _is_htmx(request):
        return render(request, "billing/partials/quote_table.html", context)
    return render(request, "billing/quote_list.html", context)


@staff_login_required
@require_http_methods(["GET"])
def quote_create(request: HttpRequest) -> HttpResponse:
    """Step 0: choose a truck to start a quote (services or supplies).

    Context:
        - trucks: QuerySet[Truck]
    """
    trucks = Truck.objects.select_related("owner", "driver").order_by("plate")
    context = {"trucks": trucks}
    template = (
        "billing/partials/quote_truck_select.html"
        if _is_htmx(request)
        else "billing/quote_truck_select.html"
    )
    return render(request, template, context)


def _parse_wizard_embeds(
    request: HttpRequest,
    line_index: int,
    supplies_by_id: dict[int, Supply],
) -> list[dict]:
    """Parse optional embedded supplies for wizard line ``lines-{index}-emb-{supply_id}-*``."""
    embeds: list[dict] = []
    for supply_id, supply in supplies_by_id.items():
        include_key = f"lines-{line_index}-emb-{supply_id}-include"
        if not request.POST.get(include_key):
            continue
        qty_raw = request.POST.get(f"lines-{line_index}-emb-{supply_id}-quantity", "1") or "1"
        cost_raw = request.POST.get(
            f"lines-{line_index}-emb-{supply_id}-cost",
            str(supply.default_cost_usd),
        ) or "0"
        try:
            quantity = Decimal(str(qty_raw))
        except Exception:
            quantity = Decimal("1")
        try:
            cost_usd = Decimal(str(cost_raw))
        except Exception:
            cost_usd = supply.default_cost_usd
        embeds.append(
            {
                "supply_id": supply_id,
                "description": supply.name,
                "quantity": quantity if quantity > 0 else Decimal("1"),
                "cost_usd": cost_usd if cost_usd >= 0 else Decimal("0"),
            }
        )
    return embeds


def _default_embeds_for_service(service: Service) -> list[dict]:
    return [
        {
            "supply_id": emb.supply_id,
            "name": emb.supply.name,
            "quantity": emb.default_quantity,
            "cost_usd": emb.default_cost_usd,
        }
        for emb in service.default_embeds.select_related("supply").all()
        if emb.supply.is_active
    ]


@staff_login_required
@require_http_methods(["GET", "POST"])
def quote_wizard(request: HttpRequest, truck_id: int, kind: str) -> HttpResponse:
    """Wizard: truck + catalog multi-select + price confirmation + BCV rate.

    Context:
        - truck: Truck
        - quote_kind: str (services|supplies)
        - kind_label: str
        - meta_form: QuoteWizardMetaForm
        - line_formset: WizardServiceFormSet | WizardSupplyFormSet
        - all_supplies: list[Supply] (services wizard only)
        - default_embeds_by_service: dict[int, list[dict]] (services wizard only)
    """
    if kind not in {QuoteKind.SERVICES, QuoteKind.SUPPLIES}:
        messages.error(request, "Tipo de presupuesto inválido.")
        return redirect("billing:quote_create")

    truck = get_object_or_404(
        Truck.objects.select_related("owner", "driver"),
        pk=truck_id,
    )
    kind_label = dict(QuoteKind.choices)[kind]
    all_supplies: list[Supply] = []
    default_embeds_by_service: dict[int, list[dict]] = {}
    supplies_by_id: dict[int, Supply] = {}

    if kind == QuoteKind.SERVICES:
        catalog_items = list(
            Service.objects.filter(is_active=True)
            .prefetch_related("default_embeds__supply")
            .order_by("name")
        )
        all_supplies = list(Supply.objects.filter(is_active=True).order_by("name"))
        supplies_by_id = {s.pk: s for s in all_supplies}
        default_embeds_by_service = {
            s.pk: _default_embeds_for_service(s) for s in catalog_items
        }
        initial = [
            {
                "selected": False,
                "service_id": s.pk,
                "name": s.name,
                "quantity": Decimal("1"),
                "catalog_price_usd": s.default_unit_price_usd,
                "unit_price_usd": s.default_unit_price_usd,
                "cost_usd": s.default_cost_usd,
            }
            for s in catalog_items
        ]
        FormSet = WizardServiceFormSet
        freshness_by_index = [price_freshness(s.price_updated_at) for s in catalog_items]
        price_dates = [s.price_updated_at for s in catalog_items]
    else:
        catalog_items = list(Supply.objects.filter(is_active=True).order_by("name"))
        initial = [
            {
                "selected": False,
                "supply_id": s.pk,
                "name": s.name,
                "quantity": Decimal("1"),
                "catalog_price_usd": s.default_unit_price_usd,
                "unit_price_usd": s.default_unit_price_usd,
                "cost_usd": s.default_cost_usd,
            }
            for s in catalog_items
        ]
        FormSet = WizardSupplyFormSet
        freshness_by_index = [price_freshness(s.price_updated_at) for s in catalog_items]
        price_dates = [s.price_updated_at for s in catalog_items]

    if request.method == "POST":
        meta_form = QuoteWizardMetaForm(request.POST)
        line_formset = FormSet(request.POST, prefix="lines")
        if meta_form.is_valid() and line_formset.is_valid():
            lines: list[dict] = []
            for index, form in enumerate(line_formset):
                if not form.cleaned_data.get("selected"):
                    continue
                if kind == QuoteKind.SERVICES:
                    service_id = form.cleaned_data["service_id"]
                    svc = next((s for s in catalog_items if s.pk == service_id), None)
                    lines.append(
                        {
                            "service_id": service_id,
                            "description": svc.name
                            if svc
                            else form.cleaned_data.get("name") or "Servicio",
                            "quantity": form.cleaned_data["quantity"],
                            "cost_usd": form.cleaned_data["cost_usd"],
                            "unit_price_usd": form.cleaned_data["unit_price_usd"],
                            "embeds": _parse_wizard_embeds(
                                request, index, supplies_by_id
                            ),
                        }
                    )
                else:
                    supply_id = form.cleaned_data["supply_id"]
                    sup = next((s for s in catalog_items if s.pk == supply_id), None)
                    lines.append(
                        {
                            "supply_id": supply_id,
                            "description": sup.name
                            if sup
                            else form.cleaned_data.get("name") or "Suministro",
                            "quantity": form.cleaned_data["quantity"],
                            "cost_usd": form.cleaned_data["cost_usd"],
                            "unit_price_usd": form.cleaned_data["unit_price_usd"],
                        }
                    )
            try:
                quote = create_quote_with_lines(
                    truck_id=truck.pk,
                    exchange_rate=meta_form.cleaned_data["exchange_rate"],
                    quote_kind=kind,
                    lines=lines,
                    notes=meta_form.cleaned_data.get("notes") or "",
                )
            except ValueError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request,
                    f"Presupuesto {quote.number} ({kind_label}) listo. "
                    "Puede enviarlo al cliente o continuar a facturación.",
                )
                return redirect("billing:quote_detail", pk=quote.pk)
        else:
            messages.error(request, "Revise la tasa BCV y los ítems seleccionados.")
    else:
        meta_form = QuoteWizardMetaForm()
        line_formset = FormSet(prefix="lines", initial=initial)

    if kind == QuoteKind.SERVICES:
        for index, form in enumerate(line_formset):
            raw_sid = form.initial.get("service_id")
            if raw_sid is None:
                raw_sid = form["service_id"].value()
            try:
                service_id = int(raw_sid)
            except (TypeError, ValueError):
                service_id = None
            defaults = {
                e["supply_id"]: e
                for e in default_embeds_by_service.get(service_id or -1, [])
            }
            rows = []
            for supply in all_supplies:
                include_key = f"lines-{index}-emb-{supply.pk}-include"
                if request.method == "POST":
                    selected = bool(request.POST.get(include_key))
                    qty_raw = request.POST.get(
                        f"lines-{index}-emb-{supply.pk}-quantity", "1"
                    )
                    cost_raw = request.POST.get(
                        f"lines-{index}-emb-{supply.pk}-cost",
                        str(supply.default_cost_usd),
                    )
                    try:
                        quantity = Decimal(str(qty_raw or "1"))
                    except Exception:
                        quantity = Decimal("1")
                    try:
                        cost_usd = Decimal(str(cost_raw or "0"))
                    except Exception:
                        cost_usd = supply.default_cost_usd
                else:
                    selected = supply.pk in defaults
                    quantity = (
                        defaults[supply.pk]["quantity"]
                        if selected
                        else Decimal("1")
                    )
                    cost_usd = (
                        defaults[supply.pk]["cost_usd"]
                        if selected
                        else supply.default_cost_usd
                    )
                rows.append(
                    {
                        "supply": supply,
                        "selected": selected,
                        "quantity": quantity,
                        "cost_usd": cost_usd,
                    }
                )
            form.embed_rows = rows
            form.has_default_embeds = bool(defaults)

    for index, form in enumerate(line_formset):
        form.freshness = (
            freshness_by_index[index]
            if index < len(freshness_by_index)
            else price_freshness(None)
        )
        form.price_updated_at = (
            price_dates[index] if index < len(price_dates) else None
        )

    context = {
        "truck": truck,
        "quote_kind": kind,
        "kind_label": kind_label,
        "meta_form": meta_form,
        "line_formset": line_formset,
        "all_supplies": all_supplies,
        "default_embeds_by_service": default_embeds_by_service,
    }
    template = (
        "billing/partials/quote_wizard.html"
        if _is_htmx(request)
        else "billing/quote_wizard.html"
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
        - can_edit_lines: bool
        - can_send: bool
        - can_accept: bool
        - can_invoice: bool
        - total_ves_equiv: Decimal
    """
    quote = get_object_or_404(
        Quote.objects.select_related("truck", "truck__owner", "truck__driver"),
        pk=pk,
    )
    copy_fiscal_rules_to_quote(quote)
    lines = list(quote.lines.select_related("service", "supply", "parent_line").all())
    billable_lines = [ln for ln in lines if not ln.is_embedded]
    embedded_lines = [ln for ln in lines if ln.is_embedded]
    can_edit_fiscal = quote.status not in {
        QuoteStatus.FACTURADO,
        QuoteStatus.ANULADO,
    }
    context = {
        "quote": quote,
        "lines": lines,
        "billable_lines": billable_lines,
        "embedded_lines": embedded_lines,
        "fiscal_rules": quote.fiscal_rules.all(),
        "iva_form": QuoteIvaForm(instance=quote),
        "convert_form": QuoteConvertForm(),
        "can_edit_fiscal": can_edit_fiscal,
        "can_send": quote.status in {
            QuoteStatus.BORRADOR,
            QuoteStatus.CONFIRMAR_PRESUPUESTO_FACTURA_ANULADA,
        },
        "can_accept": quote.status in {
            QuoteStatus.BORRADOR,
            QuoteStatus.ENVIADO,
            QuoteStatus.CONFIRMAR_PRESUPUESTO_FACTURA_ANULADA,
        },
        "can_invoice": quote.status not in {
            QuoteStatus.FACTURADO,
            QuoteStatus.ANULADO,
        } and not hasattr(quote, "invoice"),
        "total_ves_equiv": quote.total_ves_equiv,
    }
    template = (
        "billing/partials/quote_detail.html"
        if _is_htmx(request)
        else "billing/quote_detail.html"
    )
    return render(request, template, context)


@staff_login_required
@require_POST
def quote_update_iva(request: HttpRequest, pk: int) -> HttpResponse:
    """Update IVA % for this quote only and recalc totals."""
    quote = get_object_or_404(Quote, pk=pk)
    if quote.status in {QuoteStatus.FACTURADO, QuoteStatus.ANULADO}:
        messages.error(request, "No se puede editar el IVA de este presupuesto.")
        return redirect("billing:quote_detail", pk=pk)
    form = QuoteIvaForm(request.POST, instance=quote)
    if form.is_valid():
        form.save()
        refresh_quote_totals(quote)
        messages.success(request, "IVA del presupuesto actualizado.")
    else:
        messages.error(request, "IVA inválido.")
    return redirect("billing:quote_detail", pk=pk)


@staff_login_required
@require_POST
def quote_update_fiscal_rule(request: HttpRequest, pk: int, rule_pk: int) -> HttpResponse:
    """Edit a per-quote fiscal rule (percentage / active) and leave global template untouched."""
    quote = get_object_or_404(Quote, pk=pk)
    if quote.status in {QuoteStatus.FACTURADO, QuoteStatus.ANULADO}:
        messages.error(request, "No se pueden editar las reglas de este presupuesto.")
        return redirect("billing:quote_detail", pk=pk)
    rule = get_object_or_404(QuoteFiscalRule, pk=rule_pk, quote=quote)
    form = QuoteFiscalRuleEditForm(request.POST, instance=rule)
    if form.is_valid():
        form.save()
        messages.success(request, f"Regla «{rule.code}» actualizada en este presupuesto.")
    else:
        messages.error(request, "No se pudo actualizar la regla.")
    return redirect("billing:quote_detail", pk=pk)


@staff_login_required
@require_POST
def quote_mark_enviado(request: HttpRequest, pk: int) -> HttpResponse:
    """Mark quote as enviado (saved for client acceptance)."""
    quote = get_object_or_404(Quote, pk=pk)
    try:
        mark_quote_enviado(quote)
        messages.success(request, "Presupuesto marcado como enviado al cliente.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("billing:quote_detail", pk=pk)


@staff_login_required
@require_POST
def quote_mark_aceptado(request: HttpRequest, pk: int) -> HttpResponse:
    """Mark quote as aceptado."""
    quote = get_object_or_404(Quote, pk=pk)
    try:
        mark_quote_aceptado(quote)
        messages.success(request, "Presupuesto aceptado. Puede continuar a facturación.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("billing:quote_detail", pk=pk)


@staff_login_required
@require_POST
def quote_add_service_line(request: HttpRequest, pk: int) -> HttpResponse:
    """Deprecated: lines are only added in the quote wizard."""
    messages.error(
        request,
        "Los servicios y embebidos solo se agregan al crear el presupuesto.",
    )
    return redirect("billing:quote_detail", pk=pk)


@staff_login_required
@require_POST
def quote_add_supply_line(request: HttpRequest, pk: int) -> HttpResponse:
    """Deprecated: lines are only added in the quote wizard."""
    messages.error(
        request,
        "Los suministros solo se agregan al crear el presupuesto.",
    )
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
    """List invoices with optional status filter (histórico).

    Context:
        - invoices: QuerySet[Invoice]
        - status_filter: str
        - status_label: str
    """
    status_filter = request.GET.get("status", "").strip()
    invoices = Invoice.objects.select_related("quote", "quote__truck").all()
    status_label = "Todas"
    if status_filter in {c.value for c in InvoiceStatus}:
        invoices = invoices.filter(status=status_filter)
        status_label = dict(InvoiceStatus.choices).get(status_filter, status_filter)
    context = {
        "invoices": invoices,
        "status_filter": status_filter,
        "status_label": status_label,
    }
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
    """Emit invoice and generate PDF (sync or Celery)."""
    invoice = get_object_or_404(Invoice, pk=pk)
    try:
        emit_invoice(invoice)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("billing:invoice_detail", pk=pk)
    try:
        result = run_generate_document_pdf("invoice", invoice.pk)
        if result.get("status") == "queued":
            messages.success(request, "Factura emitida; PDF encolado.")
        else:
            messages.success(request, "Factura emitida; PDF generado.")
    except Exception as exc:
        messages.error(
            request,
            f"Factura emitida, pero falló el PDF: {exc.__class__.__name__}: {exc}",
        )
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
    """Generate quote PDF (sync fallback when Celery/broker unavailable)."""
    quote = get_object_or_404(Quote, pk=pk)
    refresh_quote_totals(quote)
    try:
        result = run_generate_document_pdf("quote", quote.pk)
        if result.get("status") == "queued":
            messages.success(request, "PDF de presupuesto encolado.")
        else:
            messages.success(request, "PDF de presupuesto generado.")
    except Exception as exc:
        messages.error(
            request,
            f"No se pudo generar el PDF: {exc.__class__.__name__}: {exc}",
        )
    if _is_htmx(request):
        r = HttpResponse(status=204)
        r["HX-Redirect"] = reverse("billing:quote_detail", kwargs={"pk": pk})
        r["HX-Trigger"] = "billingQuotePdfQueued"
        return r
    return redirect("billing:quote_detail", pk=pk)


@staff_login_required
@require_http_methods(["GET"])
def quote_download_pdf(request: HttpRequest, pk: int) -> HttpResponse:
    """Authenticated staff download of quote PDF."""
    from django.http import FileResponse, Http404

    quote = get_object_or_404(Quote, pk=pk)
    if not quote.pdf_file:
        raise Http404("PDF no generado aún.")
    return FileResponse(
        quote.pdf_file.open("rb"),
        as_attachment=True,
        filename=f"{quote.number}.pdf",
    )


@staff_login_required
@require_POST
def invoice_enqueue_pdf(request: HttpRequest, pk: int) -> HttpResponse:
    """Generate invoice PDF on demand."""
    invoice = get_object_or_404(Invoice, pk=pk)
    try:
        result = run_generate_document_pdf("invoice", invoice.pk)
        if result.get("status") == "queued":
            messages.success(request, "PDF de factura encolado.")
        else:
            messages.success(request, "PDF de factura generado.")
    except Exception as exc:
        messages.error(
            request,
            f"No se pudo generar el PDF: {exc.__class__.__name__}: {exc}",
        )
    return redirect("billing:invoice_detail", pk=pk)


@staff_login_required
@require_http_methods(["GET"])
def invoice_download_pdf(request: HttpRequest, pk: int) -> HttpResponse:
    """Authenticated staff download of invoice PDF."""
    from django.http import FileResponse, Http404

    invoice = get_object_or_404(Invoice, pk=pk)
    if not invoice.pdf_file:
        raise Http404("PDF no generado aún.")
    return FileResponse(
        invoice.pdf_file.open("rb"),
        as_attachment=True,
        filename=f"{invoice.number}.pdf",
    )
