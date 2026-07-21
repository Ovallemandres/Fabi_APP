"""Fleet domain models: fiscal owners, drivers, and trucks."""

from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class Owner(models.Model):
    """Propietario = cliente fiscal (RIF). Un propietario puede tener varios camiones."""

    rif = models.CharField("RIF", max_length=20, unique=True, db_index=True)
    legal_name = models.CharField("Razón social / nombre", max_length=255)
    fiscal_address = models.TextField("Dirección fiscal")
    phone = models.CharField("Teléfono", max_length=30, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Propietario"
        verbose_name_plural = "Propietarios"
        ordering = ["legal_name"]

    def __str__(self) -> str:
        return f"{self.legal_name} ({self.rif})"


class Driver(models.Model):
    """Conductor / responsable operativo (distinto del propietario fiscal)."""

    full_name = models.CharField("Nombre completo", max_length=255)
    phone = models.CharField("Teléfono", max_length=30, blank=True, default="")
    id_document = models.CharField(
        "Cédula / documento",
        max_length=30,
        blank=True,
        default="",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conductor"
        verbose_name_plural = "Conductores"
        ordering = ["full_name"]

    def __str__(self) -> str:
        return self.full_name


class TruckType(models.TextChoices):
    BASURA = "basura", "Basura"
    CESTA = "cesta", "Cesta"
    OTRO = "otro", "Otro"


class Truck(models.Model):
    """Unidad de flota asociada a un propietario fiscal y, opcionalmente, a un conductor."""

    plate = models.CharField("Placa", max_length=20, unique=True, db_index=True)
    brand = models.CharField("Marca", max_length=100)
    model = models.CharField("Modelo", max_length=100)
    vin = models.CharField(
        "VIN",
        max_length=32,
        blank=True,
        default="",
        db_index=True,
    )
    year = models.PositiveIntegerField(
        "Año",
        validators=[MinValueValidator(1950), MaxValueValidator(2100)],
    )
    truck_type = models.CharField(
        "Tipo",
        max_length=20,
        choices=TruckType.choices,
        default=TruckType.OTRO,
        db_index=True,
    )
    owner = models.ForeignKey(
        Owner,
        on_delete=models.PROTECT,
        related_name="trucks",
        verbose_name="Propietario",
    )
    # Nullable: en factura el conductor es opcional al imprimir; puede asignarse después.
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        related_name="trucks",
        verbose_name="Conductor / responsable",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Camión"
        verbose_name_plural = "Camiones"
        ordering = ["plate"]
        constraints = [
            models.CheckConstraint(
                condition=Q(year__gte=1950) & Q(year__lte=2100),
                name="fleet_truck_year_range",
            ),
            models.UniqueConstraint(
                fields=["vin"],
                condition=~Q(vin=""),
                name="fleet_truck_vin_unique_when_set",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.plate} — {self.brand} {self.model}"
