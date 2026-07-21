"""Django forms for catalog CRUD."""

from __future__ import annotations

from django import forms

from .models import Service, Supply


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ("name", "description", "is_active")


class SupplyForm(forms.ModelForm):
    class Meta:
        model = Supply
        fields = ("name", "description", "unit", "is_active")
