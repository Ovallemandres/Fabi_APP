"""Django admin registration for fleet models."""

from django.contrib import admin

from .models import Driver, Owner, Truck


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ("rif", "legal_name", "phone", "updated_at")
    search_fields = ("rif", "legal_name", "phone")
    ordering = ("legal_name",)


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("full_name", "id_document", "phone", "updated_at")
    search_fields = ("full_name", "id_document", "phone")
    ordering = ("full_name",)


@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = (
        "plate",
        "brand",
        "model",
        "year",
        "truck_type",
        "owner",
        "driver",
        "updated_at",
    )
    list_filter = ("truck_type", "year")
    search_fields = ("plate", "brand", "model", "vin", "owner__rif", "owner__legal_name")
    autocomplete_fields = ("owner", "driver")
    ordering = ("plate",)
