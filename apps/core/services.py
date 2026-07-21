"""Core services: company settings and concurrent document numbering."""

from __future__ import annotations

from django.db import transaction
from django.db.models import QuerySet

from .models import (
    CompanySettings,
    DocumentKind,
    DocumentSequence,
    FiscalRule,
)


def get_company_settings() -> CompanySettings:
    """Return the singleton company settings row."""
    return CompanySettings.get_solo()


def list_active_fiscal_rules() -> QuerySet[FiscalRule]:
    """Active fiscal rules ordered for calculation."""
    return FiscalRule.objects.filter(is_active=True).order_by("sort_order", "code")


def list_fiscal_rules(*, include_inactive: bool = False) -> QuerySet[FiscalRule]:
    qs = FiscalRule.objects.all().order_by("sort_order", "code")
    if not include_inactive:
        qs = qs.filter(is_active=True)
    return qs


@transaction.atomic
def allocate_document_number(document_kind: str, *, year: int | None = None) -> str:
    """Allocate next PRE/FAC number with row lock (Postgres select_for_update).

    Args:
        document_kind: ``quote`` or ``invoice`` (DocumentKind values).
        year: Calendar year; defaults to local current year.

    Returns:
        Formatted number, e.g. ``PRE-2026-00001``.
    """
    if document_kind not in {DocumentKind.QUOTE, DocumentKind.INVOICE}:
        raise ValueError(f"Invalid document_kind: {document_kind}")

    seq_year = year if year is not None else DocumentSequence.current_year()
    default_prefix = "PRE" if document_kind == DocumentKind.QUOTE else "FAC"

    seq, _created = DocumentSequence.objects.select_for_update().get_or_create(
        document_kind=document_kind,
        year=seq_year,
        defaults={
            "prefix": default_prefix,
            "padding": 5,
            "next_number": 1,
        },
    )
    number = seq.next_number
    seq.next_number = number + 1
    seq.save(update_fields=["next_number"])
    return f"{seq.prefix}-{seq.year}-{number:0{seq.padding}d}"
