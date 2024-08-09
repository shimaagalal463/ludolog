"""Venues where games are played."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Venue:
    id: int = 0
    name: str = ""
    address: str = ""
    default_for_nights: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "default_for_nights": self.default_for_nights,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Venue":
        return cls(
            id=int(data.get("id", 0)),
            name=str(data.get("name", "")),
            address=str(data.get("address", "")),
            default_for_nights=bool(data.get("default_for_nights", False)),
            notes=str(data.get("notes", "")),
        )


def default_venue(venues: List[Venue]) -> Optional[Venue]:
    for v in venues:
        if v.default_for_nights:
            return v
    return venues[0] if venues else None


def find_venue(venues: List[Venue], venue_id: int) -> Optional[Venue]:
    for v in venues:
        if v.id == venue_id:
            return v
    return None


def venue_play_counts(lib) -> list[tuple[str, int]]:
    from collections import Counter
    c: Counter = Counter()
    venues = {v.id: v for v in lib.venues}
    for p in lib.plays:
        if p.venue_id and p.venue_id in venues:
            c[venues[p.venue_id].name] += 1
    return c.most_common()
