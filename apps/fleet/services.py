"""Fleet business services: search and persistence helpers."""

from __future__ import annotations

from django.db.models import Prefetch, Q, QuerySet

from .models import Driver, Owner, Truck


def search_owners(query: str = "") -> QuerySet[Owner]:
    """Return owners filtered by RIF or legal name (accent/case insensitive)."""
    qs = Owner.objects.all()
    term = query.strip()
    if not term:
        return qs
    return qs.filter(
        Q(rif__icontains=term) | Q(legal_name__unaccent__icontains=term)
    )


def search_drivers(query: str = "") -> QuerySet[Driver]:
    """Return drivers filtered by name, phone or document."""
    qs = Driver.objects.all()
    term = query.strip()
    if not term:
        return qs
    return qs.filter(
        Q(full_name__unaccent__icontains=term)
        | Q(phone__icontains=term)
        | Q(id_document__icontains=term)
    )


def search_trucks(query: str = "") -> QuerySet[Truck]:
    """Return trucks with owner/driver, filtered by plate, brand, model or owner."""
    qs = Truck.objects.select_related("owner", "driver").all()
    term = query.strip()
    if not term:
        return qs
    return qs.filter(
        Q(plate__icontains=term)
        | Q(brand__unaccent__icontains=term)
        | Q(model__unaccent__icontains=term)
        | Q(vin__icontains=term)
        | Q(owner__legal_name__unaccent__icontains=term)
        | Q(owner__rif__icontains=term)
    )


def get_truck_for_detail(truck_id: int) -> Truck:
    """Load a truck with related owner and driver for detail views."""
    return Truck.objects.select_related("owner", "driver").get(pk=truck_id)


def list_trucks_for_owner(owner_id: int) -> QuerySet[Truck]:
    """List trucks belonging to a fiscal owner."""
    return (
        Truck.objects.filter(owner_id=owner_id)
        .select_related("driver")
        .order_by("plate")
    )


def owners_with_trucks() -> QuerySet[Owner]:
    """Owners with prefetched trucks for detail/list screens."""
    return Owner.objects.prefetch_related(
        Prefetch("trucks", queryset=Truck.objects.order_by("plate"))
    )
