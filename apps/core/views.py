"""Core views: health check and home (HTMX-aware)."""

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render


def health(request: HttpRequest) -> JsonResponse:
    """Smoke check for deploy and local boot verification.

    Returns JSON ``{"status": "ok"}``.
    """
    return JsonResponse({"status": "ok"})


def home(request: HttpRequest) -> HttpResponse:
    """Landing placeholder for scaffolding.

    Context:
        - app_name: str — product display name
        - status: str — bootstrap status label
    """
    context: dict[str, str] = {
        "app_name": "Fabi",
        "status": "scaffolding",
    }
    if request.headers.get("HX-Request"):
        return render(request, "partials/home_content.html", context)
    return render(request, "home.html", context)
