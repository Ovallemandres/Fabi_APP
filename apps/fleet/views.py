"""Fleet views (stubs until domain models exist)."""

from django.http import HttpRequest, HttpResponse


def index(request: HttpRequest) -> HttpResponse:
    """Placeholder index for /fleet/ so frontend can hang routes later."""
    return HttpResponse("fleet ok", content_type="text/plain")
