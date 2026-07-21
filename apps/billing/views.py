"""Billing views (stubs until domain models exist)."""

from django.http import HttpRequest, HttpResponse


def index(request: HttpRequest) -> HttpResponse:
    """Placeholder index for /billing/ so frontend can hang routes later."""
    return HttpResponse("billing ok", content_type="text/plain")
