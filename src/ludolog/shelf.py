"""Physical shelf organization."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Shelf:
    id: int = 0
    name: str = ""
    location: str = ""
    capacity: Optional[int] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "capacity": self.capacity,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Shelf":
        return cls(
            id=int(data.get("id", 0)),
            name=str(data.get("name", "")),
            location=str(data.get("location", "")),
            capacity=data.get("capacity"),
            notes=str(data.get("notes", "")),
        )

    def room_label(self) -> str:
        if self.location:
            return f"{self.name} ({self.location})"
        return self.name


def shelf_usage(games_on_shelf: int, shelf: Shelf) -> Optional[float]:
    if shelf.capacity and shelf.capacity > 0:
        return games_on_shelf / shelf.capacity
    return None


def find_shelf(shelves: List[Shelf], shelf_id: int) -> Optional[Shelf]:
    for s in shelves:
        if s.id == shelf_id:
            return s
    return None


def shelves_with_capacity(shelves: List[Shelf]) -> List[Shelf]:
    return [s for s in shelves if s.capacity]


def full_shelves(lib) -> List[Shelf]:
    out = []
    for s in lib.shelves:
        count = len([g for g in lib.games if g.shelf_id == s.id])
        if s.capacity and count >= s.capacity:
            out.append(s)
    return out
