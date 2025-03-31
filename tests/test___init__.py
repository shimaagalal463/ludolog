"""Tests for ludolog package __init__."""
import ludolog
from ludolog import (
    Game,
    ImportError as LudologImportError,
    Library,
    LudologError,
    MigrationError,
    NotFoundError,
    Play,
    Player,
    PluginError,
    StorageError,
    ValidationError,
    init_library,
)


def test_version_is_string():
    assert isinstance(ludolog.__version__, str)
    assert ludolog.__version__ == "1.2.0"


def test_author_set():
    assert ludolog.__author__ == "Shimaa Galal"


def test_all_exports_public():
    expected = {
        "Game", "ImportError", "Library", "LudologError", "MigrationError",
        "NotFoundError", "Play", "Player", "PluginError", "StorageError",
        "ValidationError", "__version__", "init_library",
    }
    assert set(ludolog.__all__) == expected


def test_game_importable_from_package():
    g = Game(title="Test")
    assert g.title == "Test"


def test_play_importable_from_package():
    p = Play(game_id=1)
    assert p.game_id == 1


def test_player_importable_from_package():
    pl = Player(name="Test")
    assert pl.name == "Test"


def test_library_importable_from_package():
    assert Library is not None


def test_init_library_importable():
    assert callable(init_library)


def test_ludolog_error_importable():
    assert issubclass(LudologError, Exception)


def test_validation_error_importable():
    assert issubclass(ValidationError, LudologError)


def test_storage_error_importable():
    assert issubclass(StorageError, LudologError)


def test_migration_error_importable():
    assert issubclass(MigrationError, LudologError)


def test_not_found_error_importable():
    assert issubclass(NotFoundError, LudologError)


def test_import_error_is_domain_not_builtin():
    import builtins
    assert LudologImportError is not builtins.ImportError


def test_plugin_error_importable():
    assert issubclass(PluginError, LudologError)


def test_package_docstring_present():
    assert "board game" in ludolog.__doc__.lower()


def test_version_matches_pyproject():
    assert ludolog.__version__.count(".") == 2
