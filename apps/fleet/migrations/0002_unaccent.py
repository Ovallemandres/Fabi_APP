"""Enable PostgreSQL unaccent for accent-insensitive fleet searches."""

from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("fleet", "0001_initial"),
    ]

    operations = [
        UnaccentExtension(),
    ]
