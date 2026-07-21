"""URL routes for the billing app."""

from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.index, name="index"),
]
