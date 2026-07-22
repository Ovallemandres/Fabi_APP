"""Catalog CRUD views with HTMX partial support."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import staff_login_required

from .forms import ServiceForm, SupplyForm
from .models import Service, ServiceDefaultEmbed, Supply
from .services import (
    activate_service,
    activate_supply,
    deactivate_service,
    deactivate_supply,
    search_services,
    search_supplies,
    sync_service_default_embeds,
)


def _is_htmx(request: HttpRequest) -> bool:
    return request.headers.get("HX-Request") == "true"


def _hx_redirect(url: str) -> HttpResponse:
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response


@staff_login_required
def index(request: HttpRequest) -> HttpResponse:
    """Catalog hub.

    Context:
        - section: str
        - services_url, supplies_url: str
        - services_meta, supplies_meta: str
    """
    context = {
        "section": "hub",
        "services_url": reverse("catalog:service_list"),
        "supplies_url": reverse("catalog:supply_list"),
        "services_meta": f"{Service.objects.filter(is_active=True).count()} activos",
        "supplies_meta": f"{Supply.objects.filter(is_active=True).count()} activos",
    }
    template = "catalog/partials/hub.html" if _is_htmx(request) else "catalog/hub.html"
    return render(request, template, context)


@staff_login_required
@require_http_methods(["GET"])
def service_list(request: HttpRequest) -> HttpResponse:
    """List / search services.

    Context:
        - services: QuerySet[Service]
        - q: str
        - include_inactive: bool
    """
    q = request.GET.get("q", "")
    include_inactive = request.GET.get("include_inactive") == "1"
    context = {
        "services": search_services(q, include_inactive=include_inactive),
        "q": q,
        "include_inactive": include_inactive,
    }
    if _is_htmx(request):
        return render(request, "catalog/partials/service_table.html", context)
    return render(request, "catalog/service_list.html", context)


def _service_form_context(
    *,
    form: ServiceForm,
    title: str,
    service: Service | None = None,
) -> dict:
    """Shared context for service create/update (default embeds UI)."""
    from decimal import Decimal

    active_supplies = list(Supply.objects.filter(is_active=True).order_by("name"))
    selected_embeds: dict[int, ServiceDefaultEmbed] = {}
    if service is not None:
        selected_embeds = {
            emb.supply_id: emb
            for emb in service.default_embeds.select_related("supply").all()
        }
    embed_rows = []
    for supply in active_supplies:
        emb = selected_embeds.get(supply.pk)
        embed_rows.append(
            {
                "supply": supply,
                "selected": emb is not None,
                "quantity": emb.default_quantity if emb else Decimal("1"),
                "cost_usd": emb.default_cost_usd if emb else supply.default_cost_usd,
            }
        )
    return {
        "form": form,
        "title": title,
        "service": service,
        "embed_rows": embed_rows,
        "embeds_panel_open": any(row["selected"] for row in embed_rows),
    }


@staff_login_required
@require_http_methods(["GET", "POST"])
def service_create(request: HttpRequest) -> HttpResponse:
    """Create a service template.

    Context:
        - form: ServiceForm
        - title: str
        - active_supplies: list[Supply]
        - selected_embeds: dict[int, ServiceDefaultEmbed]
    """
    form = ServiceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        service = form.save()
        sync_service_default_embeds(service, request)
        messages.success(request, f"Servicio {service.name} creado.")
        url = reverse("catalog:service_list")
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = _service_form_context(form=form, title="Nuevo servicio")
    template = (
        "catalog/partials/service_form.html"
        if _is_htmx(request)
        else "catalog/service_form.html"
    )
    return render(request, template, context)


@staff_login_required
@require_http_methods(["GET", "POST"])
def service_update(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a service template.

    Context:
        - form: ServiceForm
        - service: Service
        - title: str
        - active_supplies: list[Supply]
        - selected_embeds: dict[int, ServiceDefaultEmbed]
    """
    service = get_object_or_404(Service, pk=pk)
    form = ServiceForm(request.POST or None, instance=service)
    if request.method == "POST" and form.is_valid():
        form.save()
        sync_service_default_embeds(service, request)
        messages.success(request, "Servicio actualizado.")
        url = reverse("catalog:service_list")
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = _service_form_context(
        form=form, title="Editar servicio", service=service
    )
    template = (
        "catalog/partials/service_form.html"
        if _is_htmx(request)
        else "catalog/service_form.html"
    )
    return render(request, template, context)


@staff_login_required
@require_POST
def service_deactivate(request: HttpRequest, pk: int) -> HttpResponse:
    """Soft-delete a service (is_active=False)."""
    service = get_object_or_404(Service, pk=pk)
    deactivate_service(service)
    messages.success(request, f"Servicio {service.name} desactivado.")
    url = reverse("catalog:service_list")
    if _is_htmx(request):
        return _hx_redirect(url)
    return redirect(url)


@staff_login_required
@require_POST
def service_activate(request: HttpRequest, pk: int) -> HttpResponse:
    """Reactivate a service."""
    service = get_object_or_404(Service, pk=pk)
    activate_service(service)
    messages.success(request, f"Servicio {service.name} reactivado.")
    url = reverse("catalog:service_list") + "?include_inactive=1"
    if _is_htmx(request):
        return _hx_redirect(url)
    return redirect(url)


@staff_login_required
@require_http_methods(["GET"])
def supply_list(request: HttpRequest) -> HttpResponse:
    """List / search supplies.

    Context:
        - supplies: QuerySet[Supply]
        - q: str
        - include_inactive: bool
    """
    q = request.GET.get("q", "")
    include_inactive = request.GET.get("include_inactive") == "1"
    context = {
        "supplies": search_supplies(q, include_inactive=include_inactive),
        "q": q,
        "include_inactive": include_inactive,
    }
    if _is_htmx(request):
        return render(request, "catalog/partials/supply_table.html", context)
    return render(request, "catalog/supply_list.html", context)


@staff_login_required
@require_http_methods(["GET", "POST"])
def supply_create(request: HttpRequest) -> HttpResponse:
    """Create a supply template.

    Context:
        - form: SupplyForm
        - title: str
    """
    form = SupplyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        supply = form.save()
        messages.success(request, f"Suministro {supply.name} creado.")
        url = reverse("catalog:supply_list")
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "title": "Nuevo suministro"}
    template = (
        "catalog/partials/supply_form.html"
        if _is_htmx(request)
        else "catalog/supply_form.html"
    )
    return render(request, template, context)


@staff_login_required
@require_http_methods(["GET", "POST"])
def supply_update(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a supply template.

    Context:
        - form: SupplyForm
        - supply: Supply
        - title: str
    """
    supply = get_object_or_404(Supply, pk=pk)
    form = SupplyForm(request.POST or None, instance=supply)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Suministro actualizado.")
        url = reverse("catalog:supply_list")
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "supply": supply, "title": "Editar suministro"}
    template = (
        "catalog/partials/supply_form.html"
        if _is_htmx(request)
        else "catalog/supply_form.html"
    )
    return render(request, template, context)


@staff_login_required
@require_POST
def supply_deactivate(request: HttpRequest, pk: int) -> HttpResponse:
    """Soft-delete a supply (is_active=False)."""
    supply = get_object_or_404(Supply, pk=pk)
    deactivate_supply(supply)
    messages.success(request, f"Suministro {supply.name} desactivado.")
    url = reverse("catalog:supply_list")
    if _is_htmx(request):
        return _hx_redirect(url)
    return redirect(url)


@staff_login_required
@require_POST
def supply_activate(request: HttpRequest, pk: int) -> HttpResponse:
    """Reactivate a supply."""
    supply = get_object_or_404(Supply, pk=pk)
    activate_supply(supply)
    messages.success(request, f"Suministro {supply.name} reactivado.")
    url = reverse("catalog:supply_list") + "?include_inactive=1"
    if _is_htmx(request):
        return _hx_redirect(url)
    return redirect(url)
