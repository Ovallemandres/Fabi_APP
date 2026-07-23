"""Catalog domain models: service and supply templates with reference prices."""

from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Service(models.Model):
    """Plantilla de servicio. Precio de referencia editable al presupuestar."""

    name = models.CharField("Nombre", max_length=255, db_index=True)
    description = models.TextField("Descripción", blank=True, default="")
    default_unit_price_usd = models.DecimalField(
        "Precio cliente USD (referencia)",
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Se sugiere al crear el presupuesto; el usuario puede confirmarlo o cambiarlo.",
    )
    default_cost_usd = models.DecimalField(
        "Costo interno USD (referencia)",
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    price_updated_at = models.DateTimeField(
        "Precio actualizado",
        null=True,
        blank=True,
        db_index=True,
        help_text="Se actualiza al cambiar precio o costo de referencia.",
    )
    is_active = models.BooleanField("Activo", default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        if self.pk:
            try:
                previous = Service.objects.get(pk=self.pk)
            except Service.DoesNotExist:
                previous = None
            if previous is not None and (
                previous.default_unit_price_usd != self.default_unit_price_usd
                or previous.default_cost_usd != self.default_cost_usd
            ):
                self.price_updated_at = timezone.now()
        elif self.price_updated_at is None:
            self.price_updated_at = timezone.now()
        super().save(*args, **kwargs)


class Supply(models.Model):
    """Plantilla de suministro. Precio de referencia editable al presupuestar."""

    name = models.CharField("Nombre", max_length=255, db_index=True)
    description = models.TextField("Descripción", blank=True, default="")
    unit = models.CharField("Unidad", max_length=50, blank=True, default="")
    default_unit_price_usd = models.DecimalField(
        "Precio cliente USD (referencia)",
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Se sugiere al crear el presupuesto; el usuario puede confirmarlo o cambiarlo.",
    )
    default_cost_usd = models.DecimalField(
        "Costo interno USD (referencia)",
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    price_updated_at = models.DateTimeField(
        "Precio actualizado",
        null=True,
        blank=True,
        db_index=True,
        help_text="Se actualiza al cambiar precio o costo de referencia.",
    )
    is_active = models.BooleanField("Activo", default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Suministro"
        verbose_name_plural = "Suministros"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        if self.pk:
            try:
                previous = Supply.objects.get(pk=self.pk)
            except Supply.DoesNotExist:
                previous = None
            if previous is not None and (
                previous.default_unit_price_usd != self.default_unit_price_usd
                or previous.default_cost_usd != self.default_cost_usd
            ):
                self.price_updated_at = timezone.now()
        elif self.price_updated_at is None:
            self.price_updated_at = timezone.now()
        super().save(*args, **kwargs)


class ServiceDefaultEmbed(models.Model):
    """Suministro embebido por defecto al presupuestar un servicio."""

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="default_embeds",
        verbose_name="Servicio",
    )
    supply = models.ForeignKey(
        Supply,
        on_delete=models.PROTECT,
        related_name="default_for_services",
        verbose_name="Suministro",
    )
    default_quantity = models.DecimalField(
        "Cantidad por defecto",
        max_digits=18,
        decimal_places=3,
        default=Decimal("1.000"),
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    default_cost_usd = models.DecimalField(
        "Costo interno USD por defecto",
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        verbose_name = "Suministro embebido por defecto"
        verbose_name_plural = "Suministros embebidos por defecto"
        constraints = [
            models.UniqueConstraint(
                fields=["service", "supply"],
                name="catalog_servicedefaultembed_service_supply_uniq",
            ),
        ]
        ordering = ["supply__name"]

    def __str__(self) -> str:
        return f"{self.service.name} → {self.supply.name}"
