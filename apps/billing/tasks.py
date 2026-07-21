"""Celery tasks for PDF generation with WeasyPrint."""

from __future__ import annotations

import logging
from typing import Any

from celery import shared_task
from django.core.files.base import ContentFile
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


@shared_task(name="billing.generate_document_pdf")
def generate_document_pdf(document_type: str, document_id: int) -> dict[str, Any]:
    """Generate PDF for quote or invoice via WeasyPrint and store on the model.

    Args:
        document_type: ``quote`` or ``invoice``.
        document_id: Primary key of the document.

    Returns:
        Status dict with document identifiers and stored filename.
    """
    from weasyprint import HTML

    from apps.core.services import get_company_settings

    from .models import Invoice, Quote

    company = get_company_settings()

    if document_type == "quote":
        doc = Quote.objects.select_related(
            "truck", "truck__owner", "truck__driver"
        ).get(pk=document_id)
        html = render_to_string(
            "billing/pdf/quote.html",
            {"quote": doc, "company": company, "lines": doc.lines.all()},
        )
        pdf_bytes = HTML(string=html).write_pdf()
        filename = f"{doc.number}.pdf"
        doc.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
    elif document_type == "invoice":
        doc = Invoice.objects.select_related(
            "quote",
            "quote__truck",
            "quote__truck__owner",
            "quote__truck__driver",
        ).get(pk=document_id)
        billable = doc.lines.filter(is_billable=True)
        html = render_to_string(
            "billing/pdf/invoice.html",
            {
                "invoice": doc,
                "company": company,
                "billable_lines": billable,
                "snapshot": doc.calculation_snapshot,
            },
        )
        pdf_bytes = HTML(string=html).write_pdf()
        filename = f"{doc.number}.pdf"
        doc.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
    else:
        raise ValueError(f"Unknown document_type: {document_type}")

    logger.info("PDF generated: %s #%s", document_type, document_id)
    return {
        "status": "ok",
        "document_type": document_type,
        "document_id": document_id,
        "filename": filename,
    }
