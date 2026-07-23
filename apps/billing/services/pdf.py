"""PDF generation helpers (sync fallback + Celery enqueue)."""

from __future__ import annotations

import logging
from typing import Any

from celery.exceptions import OperationalError
from django.conf import settings

from apps.billing.tasks import generate_document_pdf

logger = logging.getLogger(__name__)


def run_generate_document_pdf(document_type: str, document_id: int) -> dict[str, Any]:
    """Generate PDF synchronously or via Celery according to settings / broker.

    Uses sync when ``PDF_SYNC`` is True, ``CELERY_TASK_ALWAYS_EAGER`` is True,
    or the broker is unreachable (local without Redis/worker).
    """
    use_sync = bool(getattr(settings, "PDF_SYNC", False)) or bool(
        getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)
    )
    if use_sync:
        return generate_document_pdf(document_type, document_id)

    try:
        generate_document_pdf.delay(document_type, document_id)
        return {"status": "queued", "document_type": document_type, "document_id": document_id}
    except OperationalError as exc:
        logger.warning(
            "Celery broker unavailable; generating PDF sync (%s #%s): %s",
            document_type,
            document_id,
            exc,
        )
        return generate_document_pdf(document_type, document_id)
