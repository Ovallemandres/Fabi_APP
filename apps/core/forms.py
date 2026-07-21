"""Forms for core configuration screens."""

from __future__ import annotations

from django import forms

from .models import CompanySettings, DocumentSequence, FiscalRule


class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = ("legal_name", "rif", "fiscal_address", "iva_pct")


class FiscalRuleForm(forms.ModelForm):
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


class DocumentSequenceForm(forms.ModelForm):
    class Meta:
        model = DocumentSequence
        fields = ("prefix", "padding", "next_number")
