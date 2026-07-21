"""URL routes for the fleet app."""

from django.urls import path

from . import views

app_name = "fleet"

urlpatterns = [
    path("", views.index, name="index"),
    # Owners
    path("owners/", views.owner_list, name="owner_list"),
    path("owners/new/", views.owner_create, name="owner_create"),
    path("owners/<int:pk>/", views.owner_detail, name="owner_detail"),
    path("owners/<int:pk>/edit/", views.owner_update, name="owner_update"),
    path("owners/<int:pk>/delete/", views.owner_delete, name="owner_delete"),
    # Drivers
    path("drivers/", views.driver_list, name="driver_list"),
    path("drivers/new/", views.driver_create, name="driver_create"),
    path("drivers/<int:pk>/edit/", views.driver_update, name="driver_update"),
    path("drivers/<int:pk>/delete/", views.driver_delete, name="driver_delete"),
    # Trucks
    path("trucks/", views.truck_list, name="truck_list"),
    path("trucks/new/", views.truck_create, name="truck_create"),
    path("trucks/<int:pk>/", views.truck_detail, name="truck_detail"),
    path("trucks/<int:pk>/edit/", views.truck_update, name="truck_update"),
    path("trucks/<int:pk>/delete/", views.truck_delete, name="truck_delete"),
]
