"""Django admin for catalog templates."""

from django.contrib import admin

from .models import Service, Supply


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description", "unit")
