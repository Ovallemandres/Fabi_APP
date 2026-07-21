"""Catalog views (stubs until domain models exist)."""

from django.http import HttpRequest, HttpResponse


def index(request: HttpRequest) -> HttpResponse:
    """Placeholder index for /catalog/ so frontend can hang routes later."""
    return HttpResponse("catalog ok", content_type="text/plain")
