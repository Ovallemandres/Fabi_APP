"""Django forms for fleet CRUD."""

from __future__ import annotations

from django import forms

from .models import Driver, Owner, Truck


class OwnerForm(forms.ModelForm):
    """Formulario de propietario (cliente fiscal)."""

    class Meta:
        model = Owner
        fields = ("rif", "legal_name", "fiscal_address", "phone")


class DriverForm(forms.ModelForm):
    """Formulario de conductor / responsable."""

    class Meta:
        model = Driver
        fields = ("full_name", "phone", "id_document")


class TruckForm(forms.ModelForm):
    """Formulario de camión: vehículo + propietario + conductor opcional."""

    class Meta:
        model = Truck
        fields = (
            "plate",
            "brand",
            "model",
            "vin",
            "year",
            "truck_type",
            "owner",
            "driver",
        )
