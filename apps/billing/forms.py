"""Billing forms including quote wizard from truck."""

from __future__ import annotations

from decimal import Decimal

from django import forms

from apps.catalog.models import Service, Supply
from apps.core.form_styling import NeumorphicFormMixin
from apps.fleet.models import Truck

from .models import Quote


class QuoteForm(NeumorphicFormMixin, forms.ModelForm):
    class Meta:
        model = Quote
        fields = ("truck", "exchange_rate", "notes")

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.fields["truck"].queryset = Truck.objects.select_related("owner").all()
        self.fields["exchange_rate"].label = "Tasa BCV (presupuesto)"


class QuoteConvertForm(NeumorphicFormMixin, forms.Form):
    exchange_rate = forms.DecimalField(
        label="Tasa BCV factura (nueva)",
        min_value=Decimal("0.000001"),
        max_digits=18,
        decimal_places=6,
        help_text="Obligatoria y distinta del flujo de presupuesto: recalcula todos los montos en Bs.",
    )


class QuoteWizardMetaForm(NeumorphicFormMixin, forms.Form):
    """BCV rate + notes for the truck→quote wizard."""

    exchange_rate = forms.DecimalField(
        label="Tasa BCV del presupuesto",
        min_value=Decimal("0.000001"),
        max_digits=18,
        decimal_places=6,
        help_text="Tasa de cambio del Banco Central de Venezuela (USD → VES).",
    )
    notes = forms.CharField(
        label="Notas",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class ServiceLineForm(NeumorphicFormMixin, forms.Form):
    """Service line; embeds handled via formset fields prefixed embed-."""

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


class EmbeddedSupplyForm(NeumorphicFormMixin, forms.Form):
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


class SupplyLineForm(NeumorphicFormMixin, forms.Form):
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


EmbeddedSupplyFormSet = forms.formset_factory(
    EmbeddedSupplyForm,
    extra=2,
    can_delete=False,
)


class WizardServiceLineForm(NeumorphicFormMixin, forms.Form):
    """One selectable service row in the wizard (confirm or update price)."""

    selected = forms.BooleanField(required=False, initial=False, label="Incluir")
    service_id = forms.IntegerField(widget=forms.HiddenInput)
    name = forms.CharField(
        required=False,
        label="Servicio",
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
    )
    quantity = forms.DecimalField(
        min_value=Decimal("0.001"), initial=Decimal("1"), label="Cantidad"
    )
    catalog_price_usd = forms.DecimalField(
        required=False,
        label="Precio catálogo USD",
        widget=forms.NumberInput(attrs={"readonly": "readonly", "step": "0.01"}),
    )
    unit_price_usd = forms.DecimalField(
        min_value=Decimal("0"), label="Precio a cobrar USD"
    )
    cost_usd = forms.DecimalField(min_value=Decimal("0"), label="Costo interno USD")


class WizardSupplyLineForm(NeumorphicFormMixin, forms.Form):
    """One selectable supply row in the wizard (confirm or update price)."""

    selected = forms.BooleanField(required=False, initial=False, label="Incluir")
    supply_id = forms.IntegerField(widget=forms.HiddenInput)
    name = forms.CharField(
        required=False,
        label="Suministro",
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
    )
    quantity = forms.DecimalField(
        min_value=Decimal("0.001"), initial=Decimal("1"), label="Cantidad"
    )
    catalog_price_usd = forms.DecimalField(
        required=False,
        label="Precio catálogo USD",
        widget=forms.NumberInput(attrs={"readonly": "readonly", "step": "0.01"}),
    )
    unit_price_usd = forms.DecimalField(
        min_value=Decimal("0"), label="Precio a cobrar USD"
    )
    cost_usd = forms.DecimalField(min_value=Decimal("0"), label="Costo interno USD")


WizardServiceFormSet = forms.formset_factory(WizardServiceLineForm, extra=0)
WizardSupplyFormSet = forms.formset_factory(WizardSupplyLineForm, extra=0)
