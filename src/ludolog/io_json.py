"""JSON import/export helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from .errors import ImportError as LudologImportError, StorageError
from .migrate import ensure_migrated
from .storage import Library

if TYPE_CHECKING:
    pass


def export_library_json(lib: Library, path: Path | str, pretty: bool = True) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if pretty:
        text = json.dumps(lib.to_dict(), indent=2, ensure_ascii=False)
    else:
        text = json.dumps(lib.to_dict(), ensure_ascii=False)
    p.write_text(text, encoding="utf-8")


def import_library_json(path: Path | str) -> Library:
    return Library.load(path)


def load_partial(path: Path | str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise LudologImportError("json not found")
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StorageError("invalid JSON") from exc
    return ensure_migrated(raw)


def merge_json_into(lib: Library, path: Path | str) -> int:
    data = load_partial(path)
    added = 0
    from .game import Game, find_game_by_bgg, find_game_by_title
    from .play import Play
    from .player import Player, find_player_by_name

    for gd in data.get("games", []):
        g = Game.from_dict(gd)
        if g.bgg_id and find_game_by_bgg(lib.games, g.bgg_id):
            continue
        if find_game_by_title(lib.games, g.title):
            continue
        lib.add_game(g)
        added += 1
    for pd in data.get("players", []):
        pl = Player.from_dict(pd)
        if find_player_by_name(lib.players, pl.name):
            continue
        lib.add_player(pl)
        added += 1
    for play_d in data.get("plays", []):
        lib.add_play(Play.from_dict(play_d))
        added += 1
    return added


def export_minimal(lib, path) -> None:
    from pathlib import Path
    import json
    payload = {
        "games": [g.to_dict() for g in lib.games if g.owned],
        "plays": [p.to_dict() for p in lib.plays[-100:]],
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
