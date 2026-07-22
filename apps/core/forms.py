"""Forms for core configuration screens."""

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from apps.core.form_styling import NeumorphicFormMixin

from .models import CompanySettings, DocumentSequence, FiscalRule


class StaffAuthenticationForm(NeumorphicFormMixin, AuthenticationForm):
    """Login form with neumorphic field widgets."""


class CompanySettingsForm(NeumorphicFormMixin, forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = ("legal_name", "rif", "fiscal_address", "iva_pct")


class FiscalRuleForm(NeumorphicFormMixin, forms.ModelForm):
    class Meta:
        model = FiscalRule
        fields = (
            "code",
            "name",
            "percentage",
            "base",
            "applies_to",
            "is_active",
            "sort_order",
        )


class DocumentSequenceForm(NeumorphicFormMixin, forms.ModelForm):
    class Meta:
        model = DocumentSequence
        fields = ("prefix", "padding", "next_number")
