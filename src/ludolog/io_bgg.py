"""BoardGameGeek collection import."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from .errors import ImportError as LudologImportError
from .game import Game, find_game_by_bgg, find_game_by_title
from .mechanics import normalize_mechanics
from .player_range import PlayerRange
from .playtime import Playtime

if TYPE_CHECKING:
    from .storage import Library


def import_bgg_csv(lib: "Library", path: Path | str) -> int:
    p = Path(path)
    if not p.exists():
        raise LudologImportError("bgg csv not found: %s" % p)
    count = 0
    with p.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            game = _game_from_bgg_row(row)
            if game.bgg_id and find_game_by_bgg(lib.games, game.bgg_id):
                existing = find_game_by_bgg(lib.games, game.bgg_id)
                existing.merge_from(game)
                continue
            if find_game_by_title(lib.games, game.title):
                continue
            lib.add_game(game)
            count += 1
    return count


def import_bgg_json(lib: "Library", path: Path | str) -> int:
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else raw.get("games") or raw.get("items") or []
    count = 0
    for item in items:
        game = _game_from_bgg_dict(item)
        if game.bgg_id and find_game_by_bgg(lib.games, game.bgg_id):
            find_game_by_bgg(lib.games, game.bgg_id).merge_from(game)
            continue
        if find_game_by_title(lib.games, game.title):
            continue
        lib.add_game(game)
        count += 1
    return count


def _game_from_bgg_row(row: Dict[str, str]) -> Game:
    title = (row.get("name") or row.get("title") or row.get("Object name") or "").strip()
    bgg_raw = row.get("objectid") or row.get("bgg_id") or row.get("id") or ""
    bgg_id = int(bgg_raw) if str(bgg_raw).isdigit() else None
    min_p = _int_or_none(row.get("minplayers") or row.get("Min Players"))
    max_p = _int_or_none(row.get("maxplayers") or row.get("Max Players"))
    min_t = _int_or_none(row.get("minplaytime") or row.get("Min Playtime"))
    max_t = _int_or_none(row.get("maxplaytime") or row.get("Max Playtime"))
    year = _int_or_none(row.get("yearpublished") or row.get("Year"))
    mechanics_raw = row.get("mechanics") or row.get("Mechanics") or ""
    mechanics = normalize_mechanics(mechanics_raw.replace("|", ",").split(","))
    owned = (row.get("owned") or row.get("Own") or "1").strip() not in ("0", "no", "false")
    return Game(
        title=title,
        bgg_id=bgg_id,
        designer=row.get("designer") or row.get("Designer") or "",
        publisher=row.get("publisher") or row.get("Publisher") or "",
        year=year,
        player_range=PlayerRange(min_players=min_p, max_players=max_p),
        playtime=Playtime(min_minutes=min_t, max_minutes=max_t),
        mechanics=mechanics,
        owned=owned,
        wishlist=not owned,
    )


def _game_from_bgg_dict(item: Dict[str, Any]) -> Game:
    title = str(item.get("name") or item.get("title") or "")
    bgg_id = item.get("id") or item.get("bgg_id")
    bgg_id = int(bgg_id) if bgg_id is not None else None
    pr = item.get("player_range") or {}
    pt = item.get("playtime") or {}
    return Game(
        title=title,
        bgg_id=bgg_id,
        designer=str(item.get("designer") or ""),
        year=item.get("year"),
        player_range=PlayerRange(
            min_players=pr.get("min") or item.get("min_players"),
            max_players=pr.get("max") or item.get("max_players"),
        ),
        playtime=Playtime(
            min_minutes=pt.get("min") or item.get("min_minutes"),
            max_minutes=pt.get("max") or item.get("max_minutes"),
        ),
        mechanics=normalize_mechanics(item.get("mechanics") or []),
        owned=bool(item.get("owned", True)),
    )


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return None

# TODO: support geeklist export format


def export_bgg_compatible_rows(lib) -> list[dict[str, str]]:
    rows = []
    for g in lib.games:
        rows.append({
            "Object name": g.title,
            "objectid": str(g.bgg_id or ""),
            "minplayers": str(g.player_range.min_players or ""),
            "maxplayers": str(g.player_range.max_players or ""),
            "minplaytime": str(g.playtime.min_minutes or ""),
            "maxplaytime": str(g.playtime.max_minutes or ""),
            "Own": "1" if g.owned else "0",
        })
    return rows


def normalize_bgg_header(name: str) -> str:
    return name.strip().lower().replace(" ", "")


def map_bgg_headers(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        out[normalize_bgg_header(k)] = v
    return out


def _row_get(row: dict, *keys: str) -> str:
    mapped = map_bgg_headers(row)
    for key in keys:
        nk = normalize_bgg_header(key)
        if nk in mapped and mapped[nk]:
            return str(mapped[nk])
    return ""


def import_bgg_flexible_csv(lib, path) -> int:
    import csv
    from pathlib import Path
    p = Path(path)
    count = 0
    with p.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            title = _row_get(row, "Object name", "name", "title")
            if not title:
                continue
            game = _game_from_bgg_row(row)
            from .game import find_game_by_bgg, find_game_by_title
            if game.bgg_id and find_game_by_bgg(lib.games, game.bgg_id):
                find_game_by_bgg(lib.games, game.bgg_id).merge_from(game)
                continue
            if find_game_by_title(lib.games, game.title):
                continue
            lib.add_game(game)
            count += 1
    return count


def validate_bgg_row(row: dict) -> list[str]:
    issues = []
    title = _row_get(row, "Object name", "name")
    if not title:
        issues.append("missing title")
    bgg = _row_get(row, "objectid", "id")
    if bgg and not str(bgg).isdigit():
        issues.append("invalid bgg id")
    return issues


def split_mechanics_field(raw: str) -> list[str]:
    if not raw:
        return []
    parts = raw.replace("|", ";").replace("/", ";").split(";")
    return [p.strip() for p in parts if p.strip()]
