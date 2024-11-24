"""Schema migrations 0 -> 1 -> 2 -> 3."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from .errors import MigrationError

CURRENT_SCHEMA = 3


def migrate_v0_to_v1(data: Dict[str, Any]) -> Dict[str, Any]:
    """Introduce games, plays, players, tags."""
    out = deepcopy(data)
    out.setdefault("games", [])
    out.setdefault("plays", [])
    out.setdefault("players", [])
    out.setdefault("tags", [])
    out["schema_version"] = 1
    return out


def migrate_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
    """Add shelves, venues, notes, audit log."""
    out = deepcopy(data)
    out.setdefault("shelves", [])
    out.setdefault("venues", [])
    out.setdefault("notes", [])
    out.setdefault("audit_log", [])
    out.setdefault("collections", [])
    # legacy play records may lack player_ids
    for play in out.get("plays", []):
        play.setdefault("player_ids", [])
        play.setdefault("winner_ids", [])
        play.setdefault("scores", {})
    out["schema_version"] = 2
    return out


def migrate_v2_to_v3(data: Dict[str, Any]) -> Dict[str, Any]:
    """Add seasons, goals, recurring game nights."""
    out = deepcopy(data)
    out.setdefault("seasons", [])
    out.setdefault("goals", [])
    out.setdefault("recurring_nights", [])
    for game in out.get("games", []):
        game.setdefault("mechanics", [])
        game.setdefault("owned", True)
        game.setdefault("wishlist", False)
    # FIXME: old wishlist tags like "wishlist" not auto-stripped
    out["schema_version"] = 3
    return out


_MIGRATORS = {0: migrate_v0_to_v1, 1: migrate_v1_to_v2, 2: migrate_v2_to_v3}


def ensure_migrated(data: Dict[str, Any]) -> Dict[str, Any]:
    cur = int(data.get("schema_version", 0))
    if cur > CURRENT_SCHEMA:
        raise MigrationError(
            "journal newer than this ludolog (%d > %d)" % (cur, CURRENT_SCHEMA)
        )
    while cur < CURRENT_SCHEMA:
        fn = _MIGRATORS.get(cur)
        if fn is None:
            raise MigrationError("no migrator from schema %d" % cur)
        data = fn(data)
        cur = int(data["schema_version"])
    return data


def migration_plan(data: Dict[str, Any]) -> List[int]:
    cur = int(data.get("schema_version", 0))
    steps = []
    while cur < CURRENT_SCHEMA:
        steps.append(cur)
        cur += 1
    return steps


def describe_migration(step: int) -> str:
    labels = {
        0: "bootstrap games/plays/players",
        1: "add shelves, venues, notes",
        2: "add seasons, goals, recurring nights",
    }
    return labels.get(step, "unknown")


def preview_migrations(data: dict) -> list[str]:
    plan = migration_plan(data)
    return [describe_migration(s) for s in plan]
