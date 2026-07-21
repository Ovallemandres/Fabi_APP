"""Admin for billing documents."""

from django.contrib import admin

from .models import Invoice, InvoiceLine, Quote, QuoteLine


class QuoteLineInline(admin.TabularInline):
    model = QuoteLine
    extra = 0


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("number", "truck", "status", "exchange_rate", "total_usd", "updated_at")
    list_filter = ("status",)
    search_fields = ("number", "truck__plate")
    inlines = [QuoteLineInline]


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0
    readonly_fields = (
        "line_type",
        "description",
        "quantity",
        "unit_price_usd",
        "unit_price_ves",
        "line_total_ves",
        "is_embedded",
        "is_billable",
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "quote",
        "status",
        "exchange_rate",
        "total_ves",
        "total_a_pagar_ves",
        "updated_at",
    )
    list_filter = ("status",)
    search_fields = ("number", "quote__number")
    inlines = [InvoiceLineInline]
