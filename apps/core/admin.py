"""Admin for core configuration models."""

from django.contrib import admin

from .models import CompanySettings, DocumentSequence, FiscalRule


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ("legal_name", "rif", "iva_pct", "updated_at")

    def has_add_permission(self, request) -> bool:  # type: ignore[no-untyped-def]
        return not CompanySettings.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:  # type: ignore[no-untyped-def]
        return False


@admin.register(FiscalRule)
class FiscalRuleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "percentage", "base", "applies_to", "is_active", "sort_order")
    list_filter = ("applies_to", "base", "is_active")
    search_fields = ("code", "name")


@admin.register(DocumentSequence)
class DocumentSequenceAdmin(admin.ModelAdmin):
    list_display = ("document_kind", "year", "prefix", "padding", "next_number")
    list_filter = ("document_kind", "year")
