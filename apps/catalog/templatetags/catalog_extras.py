"""Template tags for catalog price freshness badges."""

from __future__ import annotations

from datetime import datetime

from django import template

from apps.catalog.services import price_freshness

register = template.Library()

_LEVEL_CLASSES = {
    "green": "bg-emerald-100 text-emerald-800",
    "yellow": "bg-amber-100 text-amber-900",
    "red": "bg-rose-100 text-rose-800",
}


@register.inclusion_tag("catalog/partials/price_freshness_badge.html")
def price_freshness_badge(dt: datetime | None = None, freshness: dict | None = None):
    """Render a color badge for price freshness (date + level)."""
    data = freshness if freshness is not None else price_freshness(dt)
    level = data.get("level", "red")
    return {
        "level": level,
        "label": data.get("label", ""),
        "dt": dt,
        "css_class": _LEVEL_CLASSES.get(level, _LEVEL_CLASSES["red"]),
    }
