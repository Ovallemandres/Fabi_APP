"""Core models: company settings, fiscal rules, document sequences."""

from __future__ import annotations

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class CompanySettings(models.Model):
    """Singleton practical: datos del emisor + IVA global."""

    legal_name = models.CharField("Razón social", max_length=255, default="MJ SINO IMPORT, C.A.")
    rif = models.CharField("RIF", max_length=20, default="G-20013109-8")
    fiscal_address = models.TextField("Dirección fiscal", blank=True, default="")
    iva_pct = models.DecimalField(
        "IVA (%)",
        max_digits=6,
        decimal_places=4,
        default=Decimal("0.1600"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
        help_text="Fracción decimal, ej. 0.16 = 16%.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de empresa"
        verbose_name_plural = "Configuración de empresa"

    def __str__(self) -> str:
        return f"{self.legal_name} ({self.rif})"

    @classmethod
    def get_solo(cls) -> CompanySettings:
        """Return the single company settings row, creating defaults if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.pk = 1
        super().save(*args, **kwargs)


class FiscalBase(models.TextChoices):
    IVA = "iva", "Sobre IVA"
    BASE_IMPONIBLE = "base_imponible", "Sobre base imponible"


class FiscalAppliesTo(models.TextChoices):
    SERVICE = "service", "Servicios"
    SUPPLY = "supply", "Suministros"
    BOTH = "both", "Ambos"


class FiscalRule(models.Model):
    """Retención u otra regla fiscal configurable (extensible sin redeploy de fórmulas)."""

    code = models.CharField("Código", max_length=50, unique=True)
    name = models.CharField("Nombre", max_length=255)
    percentage = models.DecimalField(
        "Porcentaje",
        max_digits=8,
        decimal_places=6,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
        help_text="Fracción decimal, ej. 0.75 = 75%.",
    )
    base = models.CharField("Base", max_length=20, choices=FiscalBase.choices)
    applies_to = models.CharField(
        "Aplica a",
        max_length=20,
        choices=FiscalAppliesTo.choices,
        default=FiscalAppliesTo.BOTH,
    )
    is_active = models.BooleanField("Activo", default=True, db_index=True)
    sort_order = models.PositiveIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Regla fiscal"
        verbose_name_plural = "Reglas fiscales"
        ordering = ["sort_order", "code"]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class DocumentKind(models.TextChoices):
    QUOTE = "quote", "Presupuesto"
    INVOICE = "invoice", "Factura"


class DocumentSequence(models.Model):
    """Secuencia anual configurable PRE/FAC (next_number ajustable para facturación real)."""

    document_kind = models.CharField(max_length=20, choices=DocumentKind.choices)
    year = models.PositiveIntegerField()
    prefix = models.CharField(max_length=10)
    padding = models.PositiveSmallIntegerField(default=5)
    next_number = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Secuencia de documento"
        verbose_name_plural = "Secuencias de documentos"
        constraints = [
            models.UniqueConstraint(
                fields=["document_kind", "year"],
                name="core_documentsequence_kind_year_uniq",
            ),
        ]
        ordering = ["-year", "document_kind"]

    def __str__(self) -> str:
        return f"{self.prefix}-{self.year} next={self.next_number}"

    @classmethod
    def current_year(cls) -> int:
        return timezone.localdate().year
