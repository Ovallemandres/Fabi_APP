"""Billing domain: quotes, invoices, and document lines."""

from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class QuoteStatus(models.TextChoices):
    BORRADOR = "borrador", "Borrador"
    ENVIADO = "enviado", "Enviado"
    ACEPTADO = "aceptado", "Aceptado"
    FACTURADO = "facturado", "Facturado"
    ANULADO = "anulado", "Anulado"
    CONFIRMAR_PRESUPUESTO_FACTURA_ANULADA = (
        "confirmar_presupuesto_factura_anulada",
        "Confirmar tras factura anulada",
    )


class InvoiceStatus(models.TextChoices):
    BORRADOR = "borrador", "Borrador"
    EMITIDA = "emitida", "Emitida"
    ANULADA = "anulada", "Anulada"


class LineType(models.TextChoices):
    SERVICE = "service", "Servicio"
    SUPPLY = "supply", "Suministro"
    EMBEDDED_SUPPLY = "embedded_supply", "Suministro embebido"


class QuoteKind(models.TextChoices):
    """MVP: presupuestos de servicios y de suministros se emiten por separado."""

    SERVICES = "services", "Servicios"
    SUPPLIES = "supplies", "Suministros"


class Quote(models.Model):
    """Presupuesto en USD vinculado a un camión (1 quote → 1 invoice en MVP)."""

    number = models.CharField("Número", max_length=32, unique=True, db_index=True)
    truck = models.ForeignKey(
        "fleet.Truck",
        on_delete=models.PROTECT,
        related_name="quotes",
        verbose_name="Camión",
    )
    quote_kind = models.CharField(
        "Tipo de presupuesto",
        max_length=20,
        choices=QuoteKind.choices,
        default=QuoteKind.SERVICES,
        db_index=True,
    )
    status = models.CharField(
        max_length=40,
        choices=QuoteStatus.choices,
        default=QuoteStatus.BORRADOR,
        db_index=True,
    )
    exchange_rate = models.DecimalField(
        "Tasa BCV presupuesto",
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal("0.000001"))],
        help_text="Tasa de cambio del Banco Central (USD→VES) vigente para este presupuesto.",
    )
    subtotal_usd = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    iva_usd = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    total_usd = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    notes = models.TextField(blank=True, default="")
    pdf_file = models.FileField(upload_to="pdfs/quotes/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Presupuesto"
        verbose_name_plural = "Presupuestos"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.number

    @property
    def total_ves_equiv(self) -> Decimal:
        return (self.total_usd * self.exchange_rate).quantize(Decimal("0.01"))


class QuoteLine(models.Model):
    """Línea de presupuesto; embebidos cuelgan de un parent service line."""

    quote = models.ForeignKey(
        Quote, on_delete=models.CASCADE, related_name="lines"
    )
    line_type = models.CharField(max_length=20, choices=LineType.choices, db_index=True)
    service = models.ForeignKey(
        "catalog.Service",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    supply = models.ForeignKey(
        "catalog.Supply",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    cost_usd = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    unit_price_usd = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    is_embedded = models.BooleanField(default=False)
    parent_line = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="embedded_lines",
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Línea de presupuesto"
        verbose_name_plural = "Líneas de presupuesto"
        ordering = ["sort_order", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="billing_quoteline_quantity_positive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.quote.number}: {self.description}"

    @property
    def line_total_usd(self) -> Decimal:
        if self.is_embedded or self.line_type == LineType.EMBEDDED_SUPPLY:
            return Decimal("0.00")
        return (self.quantity * self.unit_price_usd).quantize(Decimal("0.01"))


class Invoice(models.Model):
    """Factura en VES generada desde un presupuesto (1:1)."""

    number = models.CharField("Número", max_length=32, unique=True, db_index=True)
    quote = models.OneToOneField(
        Quote,
        on_delete=models.PROTECT,
        related_name="invoice",
        verbose_name="Presupuesto",
    )
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.BORRADOR,
        db_index=True,
    )
    exchange_rate = models.DecimalField(
        "Tasa factura",
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal("0.000001"))],
    )
    base_imponible_ves = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    iva_ves = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    total_ves = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    total_retenciones_ves = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    total_a_pagar_ves = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    calculation_snapshot = models.JSONField(default=dict, blank=True)
    pdf_file = models.FileField(upload_to="pdfs/invoices/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.number


class InvoiceLine(models.Model):
    """Línea de factura (snapshot); embebidos no se muestran en PDF/UI de factura."""

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="lines"
    )
    line_type = models.CharField(max_length=20, choices=LineType.choices, db_index=True)
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price_usd = models.DecimalField(max_digits=18, decimal_places=2)
    cost_usd = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    unit_price_ves = models.DecimalField(max_digits=18, decimal_places=2)
    line_total_ves = models.DecimalField(max_digits=18, decimal_places=2)
    is_embedded = models.BooleanField(default=False)
    is_billable = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Línea de factura"
        verbose_name_plural = "Líneas de factura"
        ordering = ["sort_order", "pk"]

    def __str__(self) -> str:
        return f"{self.invoice.number}: {self.description}"
