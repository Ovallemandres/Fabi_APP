"""Celery tasks for billing documents (PDF generation)."""

import logging
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="billing.generate_document_pdf")
def generate_document_pdf(document_type: str, document_id: int) -> dict[str, Any]:
    """Enqueue contract for PDF generation of presupuesto/factura.

    Args:
        document_type: Document kind, e.g. ``"quote"`` or ``"invoice"``.
        document_id: Primary key of the document to render.

    Returns:
        Status dict confirming the stub ran (real PDF generation comes later).
    """
    # Views must only enqueue this task; never generate PDFs in the web process.
    logger.info(
        "PDF stub enqueued: document_type=%s document_id=%s",
        document_type,
        document_id,
    )
    return {
        "status": "queued_stub",
        "document_type": document_type,
        "document_id": document_id,
    }
