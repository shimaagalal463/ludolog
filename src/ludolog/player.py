"""Player model and helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Player:
    id: int = 0
    name: str = ""
    handle: str = ""
    email: str = ""
    favorite_mechanics: List[str] = field(default_factory=list)
    active: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "handle": self.handle,
            "email": self.email,
            "favorite_mechanics": list(self.favorite_mechanics),
            "active": self.active,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        return cls(
            id=int(data.get("id", 0)),
            name=str(data.get("name", "")),
            handle=str(data.get("handle", "")),
            email=str(data.get("email", "")),
            favorite_mechanics=list(data.get("favorite_mechanics", [])),
            active=bool(data.get("active", True)),
            notes=str(data.get("notes", "")),
        )

    def display_name(self) -> str:
        return self.handle or self.name

    def matches_query(self, q: str) -> bool:
        needle = q.lower()
        return needle in self.name.lower() or needle in self.handle.lower()


def find_player_by_name(players: List[Player], name: str) -> Optional[Player]:
    needle = name.strip().lower()
    for p in players:
        if p.name.lower() == needle or p.handle.lower() == needle:
            return p
    return None


def resolve_player_names(players: List[Player], names: List[str]) -> List[int]:
    ids: List[int] = []
    for raw in names:
        p = find_player_by_name(players, raw.strip())
        if p:
            ids.append(p.id)
    return ids


def active_players(players: List[Player]) -> List[Player]:
    return [p for p in players if p.active]


def inactive_players(players: List[Player]) -> List[Player]:
    return [p for p in players if not p.active]


def sort_by_name(players: List[Player]) -> List[Player]:
    return sorted(players, key=lambda p: p.name.lower())


def player_map(players: List[Player]) -> dict[int, Player]:
    return {p.id: p for p in players}


def merge_handles(players: List[Player]) -> List[str]:
    return sorted({p.handle for p in players if p.handle})
