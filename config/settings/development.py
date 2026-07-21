"""Development settings."""

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Faster static serving in local without requiring collectstatic
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
