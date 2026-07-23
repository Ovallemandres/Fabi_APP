"""Celery tasks for PDF generation (WeasyPrint, with xhtml2pdf fallback)."""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Any

from celery import shared_task
from django.core.files.base import ContentFile
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _html_to_pdf_bytes(html: str) -> tuple[bytes, str]:
    """Render HTML to PDF bytes.

    Prefer WeasyPrint (better CSS). On Windows without GTK/Pango it raises OSError;
    fall back to xhtml2pdf so local staff can still download documents.
    """
    try:
        from weasyprint import HTML

        return HTML(string=html).write_pdf(), "weasyprint"
    except (OSError, ImportError) as exc:
        logger.warning("WeasyPrint unavailable (%s); using xhtml2pdf fallback", exc)
        from xhtml2pdf import pisa

        buffer = BytesIO()
        result = pisa.CreatePDF(html, dest=buffer, encoding="utf-8")
        if result.err:
            raise RuntimeError(
                "No se pudo generar el PDF (WeasyPrint y xhtml2pdf fallaron)."
            ) from exc
        return buffer.getvalue(), "xhtml2pdf"


@shared_task(name="billing.generate_document_pdf")
def generate_document_pdf(document_type: str, document_id: int) -> dict[str, Any]:
    """Generate PDF for quote or invoice and store on the model.

    Args:
        document_type: ``quote`` or ``invoice``.
        document_id: Primary key of the document.

    Returns:
        Status dict with document identifiers and stored filename.
    """
    from apps.core.services import get_company_settings

    from .models import Invoice, LineType, Quote

    company = get_company_settings()
    engine = "unknown"

    try:
        if document_type == "quote":
            doc = Quote.objects.select_related(
                "truck", "truck__owner", "truck__driver"
            ).get(pk=document_id)
            # Client-facing PDF: never include embedded supplies.
            lines = doc.lines.filter(is_embedded=False).exclude(
                line_type=LineType.EMBEDDED_SUPPLY
            )
            html = render_to_string(
                "billing/pdf/quote.html",
                {"quote": doc, "company": company, "lines": lines},
            )
            pdf_bytes, engine = _html_to_pdf_bytes(html)
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
            pdf_bytes, engine = _html_to_pdf_bytes(html)
            filename = f"{doc.number}.pdf"
            doc.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
        else:
            raise ValueError(f"Unknown document_type: {document_type}")
    except Exception:
        logger.exception("PDF generation failed: %s #%s", document_type, document_id)
        raise

    logger.info("PDF generated via %s: %s #%s", engine, document_type, document_id)
    return {
        "status": "ok",
        "document_type": document_type,
        "document_id": document_id,
        "filename": filename,
        "engine": engine,
    }
