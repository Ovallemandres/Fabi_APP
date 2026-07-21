"""Billing forms including service line + embedded supplies formset."""

from __future__ import annotations

from decimal import Decimal

from django import forms

from apps.catalog.models import Service, Supply
from apps.fleet.models import Truck

from .models import Quote


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ("truck", "exchange_rate", "notes")

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.fields["truck"].queryset = Truck.objects.select_related("owner").all()


class QuoteConvertForm(forms.Form):
    exchange_rate = forms.DecimalField(
        label="Tasa factura",
        min_value=Decimal("0.000001"),
        max_digits=18,
        decimal_places=6,
    )


class ServiceLineForm(forms.Form):
    """Service line + metadata; embeds handled via formset fields prefixed embed-."""

    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True),
        required=False,
        label="Servicio (catálogo)",
    )
    description = forms.CharField(max_length=500, label="Descripción")
    quantity = forms.DecimalField(min_value=Decimal("0.001"), initial=Decimal("1"))
    cost_usd = forms.DecimalField(min_value=Decimal("0"), initial=Decimal("0"))
    unit_price_usd = forms.DecimalField(
        min_value=Decimal("0"), label="Precio cliente USD"
    )


class EmbeddedSupplyForm(forms.Form):
    supply = forms.ModelChoiceField(
        queryset=Supply.objects.filter(is_active=True),
        required=False,
        label="Suministro",
    )
    description = forms.CharField(max_length=500, required=False)
    quantity = forms.DecimalField(
        min_value=Decimal("0.001"), initial=Decimal("1"), required=False
    )
    cost_usd = forms.DecimalField(
        min_value=Decimal("0"), initial=Decimal("0"), required=False
    )


class SupplyLineForm(forms.Form):
    supply = forms.ModelChoiceField(
        queryset=Supply.objects.filter(is_active=True),
        required=False,
        label="Suministro (catálogo)",
    )
    description = forms.CharField(max_length=500)
    quantity = forms.DecimalField(min_value=Decimal("0.001"), initial=Decimal("1"))
    cost_usd = forms.DecimalField(min_value=Decimal("0"), initial=Decimal("0"))
    unit_price_usd = forms.DecimalField(
        min_value=Decimal("0"), label="Precio cliente USD"
    )


# Extra empty rows for embedded supplies on the same service form page.
EmbeddedSupplyFormSet = forms.formset_factory(
    EmbeddedSupplyForm,
    extra=2,
    can_delete=False,
)
