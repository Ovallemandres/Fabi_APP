"""Permission helpers and access decorators for MVP admin (staff) role."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

P = ParamSpec("P")
R = TypeVar("R", bound=HttpResponse)


def staff_login_required(view_func: Callable[P, R]) -> Callable[P, R]:
    """Require an authenticated staff user (single admin role for MVP)."""

    @wraps(view_func)
    @login_required
    def _wrapped(request: HttpRequest, *args: P.args, **kwargs: P.kwargs) -> R:
        user = request.user
        if not user.is_authenticated or not user.is_staff:
            raise PermissionDenied("Se requiere un usuario administrador (staff).")
        return view_func(request, *args, **kwargs)

    return _wrapped  # type: ignore[return-value]


def user_passes_staff(user) -> bool:
    """Return True if user is authenticated staff (for template/tests)."""
    return bool(user.is_authenticated and user.is_staff)
