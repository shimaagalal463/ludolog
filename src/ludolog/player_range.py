"""Player count ranges."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PlayerRange:
    min_players: Optional[int] = None
    max_players: Optional[int] = None
    best: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_players": self.min_players,
            "max_players": self.max_players,
            "best": self.best,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerRange":
        return cls(
            min_players=data.get("min_players"),
            max_players=data.get("max_players"),
            best=data.get("best"),
        )

    def label(self) -> str:
        if self.min_players and self.max_players:
            if self.min_players == self.max_players:
                base = str(self.min_players)
            else:
                base = f"{self.min_players}-{self.max_players}"
        elif self.max_players:
            base = f"1-{self.max_players}"
        elif self.min_players:
            base = f"{self.min_players}+"
        else:
            base = "?"
        if self.best:
            base += f" (best {self.best})"
        return base

    def fits(self, count: int) -> bool:
        lo = self.min_players or 1
        hi = self.max_players or 99
        return lo <= count <= hi


def parse_player_range(text: str) -> PlayerRange:
    text = text.strip()
    if not text:
        return PlayerRange()
    best = None
    if "best" in text.lower():
        parts = text.lower().split("best")
        text = parts[0].strip()
        try:
            best = int("".join(c for c in parts[1] if c.isdigit()))
        except ValueError:
            best = None
    if "-" in text:
        a, b = text.split("-", 1)
        try:
            return PlayerRange(min_players=int(a.strip()), max_players=int(b.strip()), best=best)
        except ValueError:
            return PlayerRange(best=best)
    if text.endswith("+"):
        try:
            return PlayerRange(min_players=int(text[:-1]), best=best)
        except ValueError:
            return PlayerRange(best=best)
    try:
        v = int(text)
        return PlayerRange(min_players=v, max_players=v, best=best)
    except ValueError:
        return PlayerRange(best=best)


def ranges_overlap(a: PlayerRange, b: PlayerRange) -> bool:
    a_lo = a.min_players or 1
    a_hi = a.max_players or 99
    b_lo = b.min_players or 1
    b_hi = b.max_players or 99
    return not (a_hi < b_lo or b_hi < a_lo)


def best_player_count(range_: PlayerRange) -> int | None:
    if range_.best:
        return range_.best
    if range_.min_players and range_.max_players:
        return (range_.min_players + range_.max_players) // 2
    return range_.max_players or range_.min_players
