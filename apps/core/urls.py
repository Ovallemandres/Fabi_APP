"""URL routes for the core app."""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("login/", views.StaffLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("settings/company/", views.company_settings_edit, name="company_settings"),
    path("settings/fiscal-rules/", views.fiscal_rule_list, name="fiscal_rule_list"),
    path(
        "settings/fiscal-rules/<int:pk>/edit/",
        views.fiscal_rule_update,
        name="fiscal_rule_update",
    ),
    path("settings/sequences/", views.sequence_list, name="sequence_list"),
    path(
        "settings/sequences/<int:pk>/edit/",
        views.sequence_update,
        name="sequence_update",
    ),
]
