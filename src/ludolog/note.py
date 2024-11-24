"""Free-form notes attached to games or plays."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Note:
    id: int = 0
    body: str = ""
    created_at: str = ""
    game_id: Optional[int] = None
    play_id: Optional[int] = None
    pinned: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "body": self.body,
            "created_at": self.created_at,
            "game_id": self.game_id,
            "play_id": self.play_id,
            "pinned": self.pinned,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Note":
        return cls(
            id=int(data.get("id", 0)),
            body=str(data.get("body", "")),
            created_at=str(data.get("created_at", "")),
            game_id=data.get("game_id"),
            play_id=data.get("play_id"),
            pinned=bool(data.get("pinned", False)),
        )


def notes_for_game(notes: list[Note], game_id: int) -> list[Note]:
    return [n for n in notes if n.game_id == game_id]


def pinned_notes(notes: list[Note]) -> list[Note]:
    return [n for n in notes if n.pinned]


def search_notes(notes: list[Note], query: str) -> list[Note]:
    q = query.lower()
    return [n for n in notes if q in n.body.lower()]


def latest_notes(notes: list[Note], limit: int = 10) -> list[Note]:
    return sorted(notes, key=lambda n: n.created_at, reverse=True)[:limit]
