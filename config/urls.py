"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("fleet/", include("apps.fleet.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("billing/", include("apps.billing.urls")),
]
