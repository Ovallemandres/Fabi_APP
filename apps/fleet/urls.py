"""URL routes for the fleet app."""

from django.urls import path

from . import views

app_name = "fleet"

urlpatterns = [
    path("", views.index, name="index"),
]
