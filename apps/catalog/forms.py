"""Django forms for catalog CRUD."""

from __future__ import annotations

from django import forms

from apps.core.form_styling import NeumorphicFormMixin

from .models import Service, Supply


class ServiceForm(NeumorphicFormMixin, forms.ModelForm):
    class Meta:
        model = Service
        fields = (
            "name",
            "description",
            "default_unit_price_usd",
            "default_cost_usd",
            "is_active",
        )


class SupplyForm(NeumorphicFormMixin, forms.ModelForm):
    class Meta:
        model = Supply
        fields = (
            "name",
            "description",
            "unit",
            "default_unit_price_usd",
            "default_cost_usd",
            "is_active",
        )
