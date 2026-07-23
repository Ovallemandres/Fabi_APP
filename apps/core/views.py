"""Core views: health, home, and authentication."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import staff_login_required

from .forms import (
    DocumentSequenceForm,
    FiscalRuleForm,
    StaffAuthenticationForm,
)
from .models import DocumentSequence, FiscalRule
from .services import list_fiscal_rules


def health(request: HttpRequest) -> JsonResponse:
    """Smoke check for deploy and local boot verification (public).

    Returns JSON ``{"status": "ok"}``.
    """
    return JsonResponse({"status": "ok"})


@staff_login_required
def home(request: HttpRequest) -> HttpResponse:
    """Landing placeholder for scaffolding.

    Context:
        - app_name: str — product display name
        - status: str — bootstrap status label
    """
    context: dict[str, str] = {
        "app_name": "Fabi",
        "status": "ready",
    }
    if request.headers.get("HX-Request"):
        return render(request, "partials/home_content.html", context)
    return render(request, "home.html", context)


class StaffLoginView(LoginView):
    """Staff-only login form for the MVP single-admin role."""

    template_name = "core/login.html"
    authentication_form = StaffAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):  # type: ignore[no-untyped-def]
        response = super().form_valid(form)
        user = self.request.user
        if not user.is_staff:
            logout(self.request)
            form.add_error(None, "Este usuario no tiene acceso de administrador.")
            return self.form_invalid(form)
        return response


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    """Log out the current user and redirect to login."""
    logout(request)
    return redirect(reverse_lazy("core:login"))


@staff_login_required
def settings_hub(request: HttpRequest) -> HttpResponse:
    """Configuration section hub (templates + sequences; issuer only via admin).

    Context:
        - fiscal_url, sequences_url: str
    """
    context = {
        "fiscal_url": reverse("core:fiscal_rule_list"),
        "sequences_url": reverse("core:sequence_list"),
    }
    if request.headers.get("HX-Request") == "true":
        return render(request, "core/partials/settings_hub.html", context)
    return render(request, "core/settings_hub.html", context)


def _is_htmx(request: HttpRequest) -> bool:
    return request.headers.get("HX-Request") == "true"


def _hx_redirect(url: str) -> HttpResponse:
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response


@staff_login_required
@require_http_methods(["GET", "POST"])
def company_settings_edit(request: HttpRequest) -> HttpResponse:
    """Issuer data is admin-only; redirect staff to settings hub."""
    messages.info(
        request,
        "Los datos del emisor solo se editan en el panel de administración (/admin/).",
    )
    return redirect("core:settings_hub")


@staff_login_required
@require_http_methods(["GET"])
def fiscal_rule_list(request: HttpRequest) -> HttpResponse:
    """List fiscal rules.

    Context:
        - rules: QuerySet[FiscalRule]
        - include_inactive: bool
    """
    include_inactive = request.GET.get("include_inactive") == "1"
    context = {
        "rules": list_fiscal_rules(include_inactive=include_inactive),
        "include_inactive": include_inactive,
    }
    if _is_htmx(request):
        return render(request, "core/partials/fiscal_rule_table.html", context)
    return render(request, "core/fiscal_rule_list.html", context)


@staff_login_required
@require_http_methods(["GET", "POST"])
def fiscal_rule_update(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a fiscal rule.

    Context:
        - form: FiscalRuleForm
        - rule: FiscalRule
        - title: str
    """
    rule = get_object_or_404(FiscalRule, pk=pk)
    form = FiscalRuleForm(request.POST or None, instance=rule)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Regla fiscal actualizada.")
        url = reverse("core:fiscal_rule_list")
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "rule": rule, "title": "Editar regla fiscal"}
    template = (
        "core/partials/fiscal_rule_form.html"
        if _is_htmx(request)
        else "core/fiscal_rule_form.html"
    )
    return render(request, template, context)


@staff_login_required
@require_http_methods(["GET"])
def sequence_list(request: HttpRequest) -> HttpResponse:
    """List document number sequences.

    Context:
        - sequences: QuerySet[DocumentSequence]
    """
    context = {"sequences": DocumentSequence.objects.all()}
    if _is_htmx(request):
        return render(request, "core/partials/sequence_table.html", context)
    return render(request, "core/sequence_list.html", context)


@staff_login_required
@require_http_methods(["GET", "POST"])
def sequence_update(request: HttpRequest, pk: int) -> HttpResponse:
    """Adjust prefix / padding / next_number for real invoice alignment.

    Context:
        - form: DocumentSequenceForm
        - sequence: DocumentSequence
        - title: str
    """
    sequence = get_object_or_404(DocumentSequence, pk=pk)
    form = DocumentSequenceForm(request.POST or None, instance=sequence)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Secuencia actualizada.")
        url = reverse("core:sequence_list")
        if _is_htmx(request):
            return _hx_redirect(url)
        return redirect(url)
    context = {"form": form, "sequence": sequence, "title": "Editar secuencia"}
    template = (
        "core/partials/sequence_form.html"
        if _is_htmx(request)
        else "core/sequence_form.html"
    )
    return render(request, template, context)
