"""Catalog business services: search, soft-deactivate, price freshness."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db import transaction
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django.utils import timezone

from .models import Service, ServiceDefaultEmbed, Supply

FRESH_DAYS = 14
STALE_DAYS = 45


def price_freshness(dt: datetime | None) -> dict[str, str]:
    """Return traffic-light level/label for catalog price age.

    - green: < 14 days
    - yellow: 14–45 days
    - red: > 45 days or missing date
    """
    if dt is None:
        return {"level": "red", "label": "Sin fecha de precio"}
    now = timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    age = now - dt
    if age < timedelta(days=FRESH_DAYS):
        return {"level": "green", "label": "Precio reciente"}
    if age <= timedelta(days=STALE_DAYS):
        return {"level": "yellow", "label": "Precio a revisar"}
    return {"level": "red", "label": "Precio desactualizado"}


def attach_price_freshness(items: list[Any]) -> list[Any]:
    """Attach ``freshness`` dict on each item for templates."""
    for item in items:
        item.freshness = price_freshness(getattr(item, "price_updated_at", None))
    return items


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


@transaction.atomic
def sync_service_default_embeds(service: Service, request: HttpRequest) -> None:
    """Replace default embeds from POST checkboxes ``embed_supply_<id>``.

    Optional companion fields: ``embed_qty_<id>``, ``embed_cost_<id>``.
    """
    selected_ids: list[int] = []
    for key, value in request.POST.items():
        if not key.startswith("embed_supply_"):
            continue
        if value in {"", "0", "false", "off"}:
            continue
        try:
            selected_ids.append(int(key.removeprefix("embed_supply_")))
        except ValueError:
            continue

    supplies = {
        s.pk: s for s in Supply.objects.filter(pk__in=selected_ids, is_active=True)
    }
    ServiceDefaultEmbed.objects.filter(service=service).exclude(
        supply_id__in=supplies.keys()
    ).delete()

    for supply_id, supply in supplies.items():
        qty_raw = request.POST.get(f"embed_qty_{supply_id}", "1") or "1"
        cost_raw = request.POST.get(f"embed_cost_{supply_id}", "") or str(
            supply.default_cost_usd
        )
        try:
            qty = Decimal(str(qty_raw))
        except (InvalidOperation, TypeError):
            qty = Decimal("1")
        try:
            cost = Decimal(str(cost_raw))
        except (InvalidOperation, TypeError):
            cost = supply.default_cost_usd
        if qty <= 0:
            qty = Decimal("1")
        if cost < 0:
            cost = Decimal("0")

        ServiceDefaultEmbed.objects.update_or_create(
            service=service,
            supply=supply,
            defaults={
                "default_quantity": qty,
                "default_cost_usd": cost,
            },
        )
