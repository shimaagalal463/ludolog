"""Chronological activity timeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .game import Game
    from .play import Play
    from .storage import Library


@dataclass
class TimelineEvent:
    when: str
    kind: str
    summary: str
    ref_id: int


def build_timeline(lib: "Library", limit: int = 50) -> List[TimelineEvent]:
    events: List[TimelineEvent] = []
    games_by_id = {g.id: g for g in lib.games}
    for play in lib.plays:
        title = games_by_id.get(play.game_id)
        name = title.title if title else f"game #{play.game_id}"
        events.append(
            TimelineEvent(
                when=play.played_at,
                kind="play",
                summary="Played {} with {} players".format(name, play.player_count()),
                ref_id=play.id,
            )
        )
    for note in lib.notes:
        events.append(
            TimelineEvent(
                when=note.created_at or "",
                kind="note",
                summary=note.body[:80],
                ref_id=note.id,
            )
        )
    events.sort(key=lambda e: e.when, reverse=True)
    return events[:limit]


def timeline_for_game(plays: List["Play"], game: "Game") -> List[TimelineEvent]:
    from .play import sort_plays_newest, plays_for_game

    out = []
    for play in sort_plays_newest(plays_for_game(plays, game.id)):
        out.append(
            TimelineEvent(
                when=play.played_at,
                kind="play",
                summary=f"{game.title} — {play.player_count()}p",
                ref_id=play.id,
            )
        )
    return out


def timeline_as_text(lib, limit: int = 30) -> str:
    lines = []
    for ev in build_timeline(lib, limit=limit):
        lines.append(f"{ev.when}\t[{ev.kind}] {ev.summary}")
    return "\n".join(lines)


# TODO: export timeline as ICS for calendar apps


def filter_timeline(events: list, kind: str) -> list:
    return [e for e in events if e.kind == kind]


def merge_timelines(*event_lists: list) -> list:
    merged = []
    for events in event_lists:
        merged.extend(events)
    merged.sort(key=lambda e: e.when, reverse=True)
    return merged


def group_timeline_by_day(lib, limit: int = 100) -> dict[str, list]:
    from collections import defaultdict
    buckets: dict[str, list] = defaultdict(list)
    for ev in build_timeline(lib, limit=limit):
        day = ev.when[:10] if ev.when else "unknown"
        buckets[day].append(ev)
    return dict(buckets)
