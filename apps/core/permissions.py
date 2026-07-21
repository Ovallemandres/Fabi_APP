"""Permission helpers for future multi-user roles (MVP: staff admin only)."""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser


def is_admin(user: AbstractBaseUser | None) -> bool:
    """MVP: only staff users are treated as administrators."""
    return bool(user is not None and user.is_authenticated and getattr(user, "is_staff", False))
