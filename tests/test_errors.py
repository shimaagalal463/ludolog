"""Tests for ludolog.errors."""
import pytest

from ludolog.errors import (
    ImportError as LudologImportError,
    LudologError,
    MigrationError,
    NotFoundError,
    PluginError,
    StorageError,
    ValidationError,
    format_error,
)


def test_ludolog_error_is_exception():
    assert issubclass(LudologError, Exception)


def test_validation_error_inherits_ludolog_error():
    assert issubclass(ValidationError, LudologError)


def test_storage_error_inherits_ludolog_error():
    assert issubclass(StorageError, LudologError)


def test_migration_error_inherits_ludolog_error():
    assert issubclass(MigrationError, LudologError)


def test_not_found_error_inherits_ludolog_error():
    assert issubclass(NotFoundError, LudologError)


def test_import_error_inherits_ludolog_error():
    assert issubclass(LudologImportError, LudologError)


def test_plugin_error_inherits_ludolog_error():
    assert issubclass(PluginError, LudologError)


def test_format_error_includes_class_name():
    exc = ValidationError("bad input")
    assert format_error(exc) == "ValidationError: bad input"


def test_format_error_storage():
    exc = StorageError("disk full")
    assert "StorageError" in format_error(exc)
    assert "disk full" in format_error(exc)


def test_format_error_not_found():
    exc = NotFoundError("game 99 not found")
    assert format_error(exc).startswith("NotFoundError:")


def test_validation_error_message_preserved():
    with pytest.raises(ValidationError, match="empty"):
        raise ValidationError("field cannot be empty")


def test_migration_error_message_preserved():
    with pytest.raises(MigrationError, match="schema"):
        raise MigrationError("schema mismatch")


def test_not_found_error_catchable_as_ludolog_error():
    with pytest.raises(LudologError):
        raise NotFoundError("missing")


def test_import_error_distinct_from_builtin():
    import builtins
    assert LudologImportError is not builtins.ImportError


def test_plugin_error_message():
    exc = PluginError("plugin load failed")
    assert str(exc) == "plugin load failed"


def test_all_errors_have_distinct_names():
    names = {ValidationError, StorageError, MigrationError, NotFoundError,
             LudologImportError, PluginError}
    assert len(names) == 6
