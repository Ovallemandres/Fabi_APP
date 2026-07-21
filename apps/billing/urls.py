"""URL routes for the billing app."""

from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.index, name="index"),
    path("quotes/", views.quote_list, name="quote_list"),
    path("quotes/new/", views.quote_create, name="quote_create"),
    path("quotes/<int:pk>/", views.quote_detail, name="quote_detail"),
    path(
        "quotes/<int:pk>/lines/service/",
        views.quote_add_service_line,
        name="quote_add_service_line",
    ),
    path(
        "quotes/<int:pk>/lines/supply/",
        views.quote_add_supply_line,
        name="quote_add_supply_line",
    ),
    path("quotes/<int:pk>/convert/", views.quote_convert, name="quote_convert"),
    path("quotes/<int:pk>/pdf/", views.quote_enqueue_pdf, name="quote_enqueue_pdf"),
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("invoices/<int:pk>/emit/", views.invoice_emit, name="invoice_emit"),
    path("invoices/<int:pk>/void/", views.invoice_void, name="invoice_void"),
]
