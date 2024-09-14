"""ludolog exceptions."""
from __future__ import annotations


class LudologError(Exception):
    """Base error for ludolog."""


class ValidationError(LudologError):
    """Bad user input or model state."""


class StorageError(LudologError):
    """JSON read/write problems."""


class MigrationError(LudologError):
    """Schema migration failed."""


class NotFoundError(LudologError):
    """Entity missing from the library."""


class ImportError(LudologError):
    """External format import failed."""  # noqa: A001 — domain name


class PluginError(LudologError):
    """Plugin load/run failure."""


def format_error(exc: LudologError) -> str:
    return f"{exc.__class__.__name__}: {exc}"
