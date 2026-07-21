"""Catalog CRUD views with HTMX partial support."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import staff_login_required

from .forms import ServiceForm, SupplyForm
from .models import Service, Supply
from .services import (
    activate_service,
    activate_supply,
    deactivate_service,
    deactivate_supply,
    search_services,
    search_supplies,
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
    """
    context = {"section": "hub"}
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


@staff_login_required
@require_http_methods(["GET", "POST"])
def service_create(request: HttpRequest) -> HttpResponse:
    """Create a service template.

    Context:
        - form: ServiceForm
        - title: str
    """
    form = ServiceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        service = form.save()
        messages.success(request, f"Servicio {service.name} creado.")
        url = reverse("catalog:service_list")
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "title": "Nuevo servicio"}
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
    """
    service = get_object_or_404(Service, pk=pk)
    form = ServiceForm(request.POST or None, instance=service)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Servicio actualizado.")
        url = reverse("catalog:service_list")
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "service": service, "title": "Editar servicio"}
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
