"""Fleet CRUD views with HTMX partial support."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import staff_login_required

from .forms import DriverForm, OwnerForm, TruckForm
from .models import Driver, Owner, Truck
from .services import (
    list_trucks_for_owner,
    search_drivers,
    search_owners,
    search_trucks,
)


def _is_htmx(request: HttpRequest) -> bool:
    return request.headers.get("HX-Request") == "true"


def _hx_redirect(url: str) -> HttpResponse:
    """HTMX client-side redirect via HX-Redirect header."""
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response


@staff_login_required
def index(request: HttpRequest) -> HttpResponse:
    """Fleet hub: entry point to owners, drivers and trucks.

    Context:
        - section: str
        - owners_url, trucks_url, drivers_url: str
        - owners_meta, trucks_meta, drivers_meta: str
    """
    context = {
        "section": "hub",
        "owners_url": reverse("fleet:owner_list"),
        "trucks_url": reverse("fleet:truck_list"),
        "drivers_url": reverse("fleet:driver_list"),
        "owners_meta": f"{Owner.objects.count()} registrados",
        "trucks_meta": f"{Truck.objects.count()} unidades",
        "drivers_meta": f"{Driver.objects.count()} conductores",
    }
    template = "fleet/partials/hub.html" if _is_htmx(request) else "fleet/hub.html"
    return render(request, template, context)


# --- Owners ---


@staff_login_required
@require_http_methods(["GET"])
def owner_list(request: HttpRequest) -> HttpResponse:
    """List / search fiscal owners.

    Context:
        - owners: QuerySet[Owner]
        - q: str — search term
        - form: OwnerForm | None — unused on list; reserved for consistency
    """
    q = request.GET.get("q", "")
    context = {
        "owners": search_owners(q),
        "q": q,
    }
    if _is_htmx(request):
        return render(request, "fleet/partials/owner_table.html", context)
    return render(request, "fleet/owner_list.html", context)


@staff_login_required
@require_http_methods(["GET", "POST"])
def owner_create(request: HttpRequest) -> HttpResponse:
    """Create a fiscal owner.

    Context:
        - form: OwnerForm
        - title: str
    """
    form = OwnerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        owner = form.save()
        messages.success(request, f"Propietario {owner.legal_name} creado.")
        url = reverse("fleet:owner_detail", kwargs={"pk": owner.pk})
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "title": "Nuevo propietario"}
    template = (
        "fleet/partials/owner_form.html" if _is_htmx(request) else "fleet/owner_form.html"
    )
    return render(request, template, context)


@staff_login_required
@require_http_methods(["GET"])
def owner_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Owner detail with related trucks.

    Context:
        - owner: Owner
        - trucks: QuerySet[Truck]
    """
    owner = get_object_or_404(Owner, pk=pk)
    context = {
        "owner": owner,
        "trucks": list_trucks_for_owner(owner.pk),
    }
    template = (
        "fleet/partials/owner_detail.html"
        if _is_htmx(request)
        else "fleet/owner_detail.html"
    )
    return render(request, template, context)


@staff_login_required
@require_http_methods(["GET", "POST"])
def owner_update(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a fiscal owner.

    Context:
        - form: OwnerForm
        - owner: Owner
        - title: str
    """
    owner = get_object_or_404(Owner, pk=pk)
    form = OwnerForm(request.POST or None, instance=owner)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Propietario actualizado.")
        url = reverse("fleet:owner_detail", kwargs={"pk": owner.pk})
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "owner": owner, "title": "Editar propietario"}
    template = (
        "fleet/partials/owner_form.html" if _is_htmx(request) else "fleet/owner_form.html"
    )
    return render(request, template, context)


@staff_login_required
@require_POST
def owner_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete owner if no protected trucks block it."""
    owner = get_object_or_404(Owner, pk=pk)
    if owner.trucks.exists():
        messages.error(
            request,
            "No se puede eliminar: el propietario tiene camiones asociados.",
        )
        url = reverse("fleet:owner_detail", kwargs={"pk": owner.pk})
    else:
        owner.delete()
        messages.success(request, "Propietario eliminado.")
        url = reverse("fleet:owner_list")
    if _is_htmx(request):
        response = HttpResponse(status=204)
        response["HX-Redirect"] = url
        response["HX-Trigger"] = "fleetOwnerDeleted"
        return response
    return redirect(url)


# --- Drivers ---


@staff_login_required
@require_http_methods(["GET"])
def driver_list(request: HttpRequest) -> HttpResponse:
    """List / search drivers.

    Context:
        - drivers: QuerySet[Driver]
        - q: str
    """
    q = request.GET.get("q", "")
    context = {"drivers": search_drivers(q), "q": q}
    if _is_htmx(request):
        return render(request, "fleet/partials/driver_table.html", context)
    return render(request, "fleet/driver_list.html", context)


@staff_login_required
@require_http_methods(["GET", "POST"])
def driver_create(request: HttpRequest) -> HttpResponse:
    """Create a driver.

    Context:
        - form: DriverForm
        - title: str
    """
    form = DriverForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        driver = form.save()
        messages.success(request, f"Conductor {driver.full_name} creado.")
        url = reverse("fleet:driver_list")
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "title": "Nuevo conductor"}
    template = (
        "fleet/partials/driver_form.html"
        if _is_htmx(request)
        else "fleet/driver_form.html"
    )
    return render(request, template, context)


@staff_login_required
@require_http_methods(["GET", "POST"])
def driver_update(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a driver.

    Context:
        - form: DriverForm
        - driver: Driver
        - title: str
    """
    driver = get_object_or_404(Driver, pk=pk)
    form = DriverForm(request.POST or None, instance=driver)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Conductor actualizado.")
        url = reverse("fleet:driver_list")
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "driver": driver, "title": "Editar conductor"}
    template = (
        "fleet/partials/driver_form.html"
        if _is_htmx(request)
        else "fleet/driver_form.html"
    )
    return render(request, template, context)


@staff_login_required
@require_POST
def driver_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete a driver (trucks keep SET_NULL)."""
    driver = get_object_or_404(Driver, pk=pk)
    driver.delete()
    messages.success(request, "Conductor eliminado.")
    url = reverse("fleet:driver_list")
    if _is_htmx(request):
        response = HttpResponse(status=204)
        response["HX-Redirect"] = url
        response["HX-Trigger"] = "fleetDriverDeleted"
        return response
    return redirect(url)


# --- Trucks ---


@staff_login_required
@require_http_methods(["GET"])
def truck_list(request: HttpRequest) -> HttpResponse:
    """List / search trucks (MVP entry: select existing unit).

    Context:
        - trucks: QuerySet[Truck]
        - q: str
    """
    q = request.GET.get("q", "")
    context = {"trucks": search_trucks(q), "q": q}
    if _is_htmx(request):
        return render(request, "fleet/partials/truck_table.html", context)
    return render(request, "fleet/truck_list.html", context)


@staff_login_required
@require_http_methods(["GET", "POST"])
def truck_create(request: HttpRequest) -> HttpResponse:
    """Create a truck with owner and optional driver.

    Context:
        - form: TruckForm
        - title: str
    """
    form = TruckForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        truck = form.save()
        messages.success(request, f"Camión {truck.plate} creado.")
        url = reverse("fleet:truck_detail", kwargs={"pk": truck.pk})
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "title": "Nuevo camión"}
    template = (
        "fleet/partials/truck_form.html" if _is_htmx(request) else "fleet/truck_form.html"
    )
    return render(request, template, context)


@staff_login_required
@require_http_methods(["GET"])
def truck_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Truck detail for selection before budgeting.

    Context:
        - truck: Truck (with owner, driver)
    """
    truck = get_object_or_404(
        Truck.objects.select_related("owner", "driver"),
        pk=pk,
    )
    context = {"truck": truck}
    template = (
        "fleet/partials/truck_detail.html"
        if _is_htmx(request)
        else "fleet/truck_detail.html"
    )
    return render(request, template, context)


@staff_login_required
@require_http_methods(["GET", "POST"])
def truck_update(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a truck.

    Context:
        - form: TruckForm
        - truck: Truck
        - title: str
    """
    truck = get_object_or_404(Truck, pk=pk)
    form = TruckForm(request.POST or None, instance=truck)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Camión actualizado.")
        url = reverse("fleet:truck_detail", kwargs={"pk": truck.pk})
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "truck": truck, "title": "Editar camión"}
    template = (
        "fleet/partials/truck_form.html" if _is_htmx(request) else "fleet/truck_form.html"
    )
    return render(request, template, context)


@staff_login_required
@require_POST
def truck_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete a truck (PROTECT on owner keeps owner intact)."""
    truck = get_object_or_404(Truck, pk=pk)
    plate = truck.plate
    truck.delete()
    messages.success(request, f"Camión {plate} eliminado.")
    url = reverse("fleet:truck_list")
    if _is_htmx(request):
        response = HttpResponse(status=204)
        response["HX-Redirect"] = url
        response["HX-Trigger"] = "fleetTruckDeleted"
        return response
    return redirect(url)
