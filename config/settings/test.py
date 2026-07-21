"""Test settings: eager Celery, isolated DB name suffix."""

from .base import *  # noqa: F403

DEBUG = False
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

DATABASES["default"]["NAME"] = env(  # noqa: F405
    "DB_NAME_TEST",
    default=f"{DATABASES['default']['NAME']}_test",  # noqa: F405
)
