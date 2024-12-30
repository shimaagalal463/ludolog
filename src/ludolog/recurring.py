"""Recurring game night schedules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


@dataclass
class RecurringNight:
    id: int = 0
    name: str = ""
    weekday: str = "fri"
    start_time: str = "19:00"
    default_venue_id: Optional[int] = None
    usual_player_ids: List[int] = field(default_factory=list)
    preferred_game_ids: List[int] = field(default_factory=list)
    active: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "weekday": self.weekday,
            "start_time": self.start_time,
            "default_venue_id": self.default_venue_id,
            "usual_player_ids": list(self.usual_player_ids),
            "preferred_game_ids": list(self.preferred_game_ids),
            "active": self.active,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecurringNight":
        return cls(
            id=int(data.get("id", 0)),
            name=str(data.get("name", "")),
            weekday=str(data.get("weekday", "fri")).lower()[:3],
            start_time=str(data.get("start_time", "19:00")),
            default_venue_id=data.get("default_venue_id"),
            usual_player_ids=[int(x) for x in data.get("usual_player_ids", [])],
            preferred_game_ids=[int(x) for x in data.get("preferred_game_ids", [])],
            active=bool(data.get("active", True)),
            notes=str(data.get("notes", "")),
        )

    def weekday_label(self) -> str:
        w = self.weekday.lower()[:3]
        for d in WEEKDAYS:
            if d == w:
                return d.capitalize()
        return self.weekday


def active_nights(nights: List[RecurringNight]) -> List[RecurringNight]:
    return [n for n in nights if n.active]


def nights_on_weekday(nights: List[RecurringNight], weekday: str) -> List[RecurringNight]:
    w = weekday.lower()[:3]
    return [n for n in nights if n.weekday[:3] == w and n.active]


def next_night_label(night: RecurringNight) -> str:
    return f"{night.weekday_label()}s {night.start_time} — {night.name}"


def suggest_games_for_night(night: RecurringNight, lib) -> list:
    from .game import Game
    games = {g.id: g for g in lib.games}
    return [games[gid] for gid in night.preferred_game_ids if gid in games]


def attach_player_to_night(night: RecurringNight, player_id: int) -> None:
    if player_id not in night.usual_player_ids:
        night.usual_player_ids.append(player_id)


def deactivate_night(night: RecurringNight) -> None:
    night.active = False

# FIXME: does not handle holiday skips yet
