"""Catalog domain models: service and supply templates (no prices)."""

from __future__ import annotations

from django.db import models


class Service(models.Model):
    """Plantilla de servicio (mano de obra / mantenimiento). Precios van en la transacción."""

    name = models.CharField("Nombre", max_length=255, db_index=True)
    description = models.TextField("Descripción", blank=True, default="")
    is_active = models.BooleanField("Activo", default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Supply(models.Model):
    """Plantilla de suministro (autoparte / consumible). Precios van en la transacción."""

    name = models.CharField("Nombre", max_length=255, db_index=True)
    description = models.TextField("Descripción", blank=True, default="")
    unit = models.CharField("Unidad", max_length=50, blank=True, default="")
    is_active = models.BooleanField("Activo", default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Suministro"
        verbose_name_plural = "Suministros"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
