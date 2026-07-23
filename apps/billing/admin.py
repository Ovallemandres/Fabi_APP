from django.contrib import admin

from .models import Invoice, InvoiceLine, Quote, QuoteFiscalRule, QuoteLine


class QuoteLineInline(admin.TabularInline):
    model = QuoteLine
    extra = 0


class QuoteFiscalRuleInline(admin.TabularInline):
    model = QuoteFiscalRule
    extra = 0


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "quote_kind",
        "truck",
        "status",
        "iva_pct",
        "exchange_rate",
        "total_usd",
        "updated_at",
    )
    list_filter = ("status", "quote_kind")
    search_fields = ("number", "truck__plate")
    inlines = [QuoteLineInline, QuoteFiscalRuleInline]


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
