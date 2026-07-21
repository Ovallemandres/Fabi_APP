"""Catalog business services: search and soft-deactivate."""

from __future__ import annotations

from django.db.models import Q, QuerySet

from .models import Service, Supply


def search_services(query: str = "", *, include_inactive: bool = False) -> QuerySet[Service]:
    """Return services filtered by name/description; active-only by default."""
    qs = Service.objects.all()
    if not include_inactive:
        qs = qs.filter(is_active=True)
    term = query.strip()
    if not term:
        return qs
    return qs.filter(
        Q(name__unaccent__icontains=term) | Q(description__unaccent__icontains=term)
    )


def search_supplies(query: str = "", *, include_inactive: bool = False) -> QuerySet[Supply]:
    """Return supplies filtered by name/description/unit; active-only by default."""
    qs = Supply.objects.all()
    if not include_inactive:
        qs = qs.filter(is_active=True)
    term = query.strip()
    if not term:
        return qs
    return qs.filter(
        Q(name__unaccent__icontains=term)
        | Q(description__unaccent__icontains=term)
        | Q(unit__icontains=term)
    )


def deactivate_service(service: Service) -> Service:
    """Soft-delete: mark service inactive."""
    service.is_active = False
    service.save(update_fields=["is_active", "updated_at"])
    return service


def deactivate_supply(supply: Supply) -> Supply:
    """Soft-delete: mark supply inactive."""
    supply.is_active = False
    supply.save(update_fields=["is_active", "updated_at"])
    return supply


def activate_service(service: Service) -> Service:
    """Reactivate a previously deactivated service."""
    service.is_active = True
    service.save(update_fields=["is_active", "updated_at"])
    return service


def activate_supply(supply: Supply) -> Supply:
    """Reactivate a previously deactivated supply."""
    supply.is_active = True
    supply.save(update_fields=["is_active", "updated_at"])
    return supply
