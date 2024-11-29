"""Play session model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


def _parse_dt(value: str) -> datetime:
    if not value:
        return datetime.now()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.strptime(value[:10], "%Y-%m-%d")


@dataclass
class Play:
    """One logged play of a game."""

    id: int = 0
    game_id: int = 0
    played_at: str = ""
    duration_minutes: Optional[int] = None
    player_ids: List[int] = field(default_factory=list)
    winner_ids: List[int] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    venue_id: Optional[int] = None
    notes: str = ""
    incomplete: bool = False
    season_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "game_id": self.game_id,
            "played_at": self.played_at,
            "duration_minutes": self.duration_minutes,
            "player_ids": list(self.player_ids),
            "winner_ids": list(self.winner_ids),
            "scores": dict(self.scores),
            "venue_id": self.venue_id,
            "notes": self.notes,
            "incomplete": self.incomplete,
            "season_id": self.season_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Play":
        scores_raw = data.get("scores") or {}
        scores = {str(k): float(v) for k, v in scores_raw.items()}
        return cls(
            id=int(data.get("id", 0)),
            game_id=int(data.get("game_id", 0)),
            played_at=str(data.get("played_at", "")),
            duration_minutes=data.get("duration_minutes"),
            player_ids=[int(x) for x in data.get("player_ids", [])],
            winner_ids=[int(x) for x in data.get("winner_ids", [])],
            scores=scores,
            venue_id=data.get("venue_id"),
            notes=str(data.get("notes", "")),
            incomplete=bool(data.get("incomplete", False)),
            season_id=data.get("season_id"),
        )

    def played_datetime(self) -> datetime:
        return _parse_dt(self.played_at)

    def played_date(self) -> str:
        return self.played_datetime().strftime("%Y-%m-%d")

    def player_count(self) -> int:
        return len(self.player_ids)

    def has_winner(self) -> bool:
        return len(self.winner_ids) > 0

    def is_coop_win(self) -> bool:
        if not self.winner_ids:
            return False
        return set(self.winner_ids) == set(self.player_ids)

    def set_score(self, player_id: int, value: float) -> None:
        self.scores[str(player_id)] = value

    def get_score(self, player_id: int) -> Optional[float]:
        return self.scores.get(str(player_id))

    def highest_scorers(self) -> List[int]:
        if not self.scores:
            return []
        best = max(self.scores.values())
        return [int(pid) for pid, val in self.scores.items() if val == best]

    def infer_winners_from_scores(self) -> None:
        top = self.highest_scorers()
        if top:
            self.winner_ids = top


def plays_for_game(plays: List[Play], game_id: int) -> List[Play]:
    return [p for p in plays if p.game_id == game_id]


def plays_in_range(plays: List[Play], start: str, end: str) -> List[Play]:
    out = []
    for p in plays:
        d = p.played_date()
        if start <= d <= end:
            out.append(p)
    return out


def sort_plays_newest(plays: List[Play]) -> List[Play]:
    return sorted(plays, key=lambda p: p.played_at, reverse=True)


def plays_with_player(plays: List[Play], player_id: int) -> List[Play]:
    return [p for p in plays if player_id in p.player_ids]


def plays_with_winner(plays: List[Play], player_id: int) -> List[Play]:
    return [p for p in plays if player_id in p.winner_ids]


def total_duration(plays: List[Play]) -> int:
    return sum(p.duration_minutes or 0 for p in plays)


def average_duration(plays: List[Play]) -> Optional[float]:
    durs = [p.duration_minutes for p in plays if p.duration_minutes]
    if not durs:
        return None
    return sum(durs) / len(durs)


def first_play(plays: List[Play], game_id: int) -> Optional[Play]:
    game_plays = plays_for_game(plays, game_id)
    if not game_plays:
        return None
    return min(game_plays, key=lambda p: p.played_at)


def last_play(plays: List[Play], game_id: int) -> Optional[Play]:
    game_plays = plays_for_game(plays, game_id)
    if not game_plays:
        return None
    return max(game_plays, key=lambda p: p.played_at)


def days_since_last_play(plays: List[Play], game_id: int) -> Optional[int]:
    from datetime import date

    lp = last_play(plays, game_id)
    if not lp:
        return None
    played = lp.played_datetime().date()
    return (date.today() - played).days


def format_play_summary(play: Play, game_title: str = "") -> str:
    title = game_title or f"game #{play.game_id}"
    dur = f", {play.duration_minutes} min" if play.duration_minutes else ""
    inc = " (incomplete)" if play.incomplete else ""
    return f"{play.played_date()} — {title}{dur}{inc}"


def merge_scores(play: Play, other: Play) -> None:
    for k, v in other.scores.items():
        play.scores[k] = v


def clear_winners(play: Play) -> None:
    play.winner_ids = []


def mark_all_winners(play: Play) -> None:
    play.winner_ids = list(play.player_ids)


def plays_on_date(plays: List[Play], date_str: str) -> List[Play]:
    return [p for p in plays if p.played_date() == date_str]


def multi_game_sessions(plays: List[Play], date_str: str) -> int:
    return len({p.game_id for p in plays_on_date(plays, date_str)})


def copy_play_template(play: Play, *, game_id: int | None = None) -> Play:
    return Play(
        game_id=game_id if game_id is not None else play.game_id,
        played_at=play.played_at,
        player_ids=list(play.player_ids),
        winner_ids=list(play.winner_ids),
        scores=dict(play.scores),
        venue_id=play.venue_id,
        notes=play.notes,
        incomplete=play.incomplete,
        season_id=play.season_id,
    )


def validate_play_roster(play: Play, known_player_ids: set[int]) -> list[str]:
    problems = []
    for pid in play.player_ids:
        if pid not in known_player_ids:
            problems.append(f"unknown player {pid}")
    for wid in play.winner_ids:
        if wid not in play.player_ids:
            problems.append(f"winner {wid} not seated")
    return problems


def duration_label(play: Play) -> str:
    if not play.duration_minutes:
        return "?"
    h, m = divmod(play.duration_minutes, 60)
    if h:
        return f"{h}h {m}m"
    return f"{m}m"
