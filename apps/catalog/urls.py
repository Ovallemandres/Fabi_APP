"""URL routes for the catalog app."""

from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.index, name="index"),
    path("services/", views.service_list, name="service_list"),
    path("services/new/", views.service_create, name="service_create"),
    path("services/<int:pk>/edit/", views.service_update, name="service_update"),
    path("services/<int:pk>/deactivate/", views.service_deactivate, name="service_deactivate"),
    path("services/<int:pk>/activate/", views.service_activate, name="service_activate"),
    path("supplies/", views.supply_list, name="supply_list"),
    path("supplies/new/", views.supply_create, name="supply_create"),
    path("supplies/<int:pk>/edit/", views.supply_update, name="supply_update"),
    path("supplies/<int:pk>/deactivate/", views.supply_deactivate, name="supply_deactivate"),
    path("supplies/<int:pk>/activate/", views.supply_activate, name="supply_activate"),
]
