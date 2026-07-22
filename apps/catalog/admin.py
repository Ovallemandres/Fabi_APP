"""Django admin for catalog templates."""

from django.contrib import admin

from .models import Service, ServiceDefaultEmbed, Supply


class ServiceDefaultEmbedInline(admin.TabularInline):
    model = ServiceDefaultEmbed
    extra = 1
    autocomplete_fields = ("supply",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "default_unit_price_usd", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    inlines = [ServiceDefaultEmbedInline]


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "default_unit_price_usd", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description", "unit")
