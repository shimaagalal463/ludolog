"""Curated game lists."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Collection:
    """Named subset of the library — party games, travel bag, etc."""

    id: int = 0
    name: str = ""
    description: str = ""
    game_ids: List[int] = field(default_factory=list)
    pinned: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "game_ids": list(self.game_ids),
            "pinned": self.pinned,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Collection":
        return cls(
            id=int(data.get("id", 0)),
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            game_ids=[int(x) for x in data.get("game_ids", [])],
            pinned=bool(data.get("pinned", False)),
        )

    def add_game(self, game_id: int) -> bool:
        if game_id not in self.game_ids:
            self.game_ids.append(game_id)
            return True
        return False

    def remove_game(self, game_id: int) -> bool:
        if game_id in self.game_ids:
            self.game_ids.remove(game_id)
            return True
        return False

    def contains(self, game_id: int) -> bool:
        return game_id in self.game_ids


def collections_for_game(collections: List[Collection], game_id: int) -> List[Collection]:
    return [c for c in collections if c.contains(game_id)]


def pinned_collections(collections: List[Collection]) -> List[Collection]:
    return [c for c in collections if c.pinned]


def collection_size(coll: Collection) -> int:
    return len(coll.game_ids)


def merge_collections(target: Collection, source: Collection) -> int:
    added = 0
    for gid in source.game_ids:
        if target.add_game(gid):
            added += 1
    return added


def collections_by_name(collections: List[Collection], name: str) -> Collection | None:
    needle = name.strip().lower()
    for c in collections:
        if c.name.strip().lower() == needle:
            return c
    return None
