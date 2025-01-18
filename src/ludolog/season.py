"""Seasonal groupings for stats."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Season:
    id: int = 0
    name: str = ""
    start_date: str = ""
    end_date: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Season":
        return cls(
            id=int(data.get("id", 0)),
            name=str(data.get("name", "")),
            start_date=str(data.get("start_date", "")),
            end_date=str(data.get("end_date", "")),
            notes=str(data.get("notes", "")),
        )

    def contains_date(self, date_str: str) -> bool:
        if self.start_date and date_str < self.start_date:
            return False
        if self.end_date and date_str > self.end_date:
            return False
        return True


def current_season(seasons: List[Season], today: str) -> Season | None:
    for s in seasons:
        if s.contains_date(today):
            return s
    return None


def assign_play_seasons(plays: list, seasons: List[Season]) -> None:
    for play in plays:
        if play.season_id:
            continue
        d = play.played_date()
        for s in seasons:
            if s.contains_date(d):
                play.season_id = s.id
                break


def season_play_count(season: Season, plays: list) -> int:
    return sum(1 for p in plays if season.contains_date(p.played_date()))


def list_season_names(seasons: List[Season]) -> List[str]:
    return [s.name for s in seasons]


def overlapping_seasons(seasons: List[Season]) -> List[tuple[Season, Season]]:
    pairs = []
    for i, a in enumerate(seasons):
        for b in seasons[i + 1 :]:
            if a.start_date <= b.end_date and b.start_date <= a.end_date:
                pairs.append((a, b))
    return pairs
