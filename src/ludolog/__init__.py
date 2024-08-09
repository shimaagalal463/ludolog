"""Board game collection and play session tracker."""

from .errors import (
    ImportError,
    LudologError,
    MigrationError,
    NotFoundError,
    PluginError,
    StorageError,
    ValidationError,
)
from .game import Game
from .play import Play
from .player import Player
from .storage import Library, init_library

__version__ = "1.2.0"
__author__ = "Shimaa Galal"

__all__ = [
    "Game",
    "ImportError",
    "Library",
    "LudologError",
    "MigrationError",
    "NotFoundError",
    "Play",
    "Player",
    "PluginError",
    "StorageError",
    "ValidationError",
    "__version__",
    "init_library",
]
