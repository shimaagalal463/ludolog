"""Playtime ranges in minutes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Playtime:
    min_minutes: Optional[int] = None
    max_minutes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"min_minutes": self.min_minutes, "max_minutes": self.max_minutes}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Playtime":
        return cls(
            min_minutes=data.get("min_minutes"),
            max_minutes=data.get("max_minutes"),
        )

    def label(self) -> str:
        if self.min_minutes and self.max_minutes:
            if self.min_minutes == self.max_minutes:
                return f"{self.min_minutes} min"
            return f"{self.min_minutes}-{self.max_minutes} min"
        if self.max_minutes:
            return f"≤{self.max_minutes} min"
        if self.min_minutes:
            return f"≥{self.min_minutes} min"
        return "unknown"

    def fits(self, minutes: int, slack: int = 0) -> bool:
        limit = self.max_minutes if self.max_minutes is not None else self.min_minutes
        if limit is None:
            return True
        return minutes + slack >= (self.min_minutes or 0) and minutes <= limit + slack

    def midpoint(self) -> Optional[int]:
        if self.min_minutes is not None and self.max_minutes is not None:
            return (self.min_minutes + self.max_minutes) // 2
        return self.max_minutes or self.min_minutes


def parse_playtime(text: str) -> Playtime:
    text = text.strip().lower().replace("minutes", "min").replace("mins", "min")
    if not text:
        return Playtime()
    if "-" in text:
        parts = text.replace("min", "").split("-")
        try:
            lo = int(parts[0].strip())
            hi = int(parts[1].strip())
            return Playtime(min_minutes=lo, max_minutes=hi)
        except (ValueError, IndexError):
            return Playtime()
    digits = "".join(c if c.isdigit() else " " for c in text).split()
    if len(digits) >= 2:
        return Playtime(min_minutes=int(digits[0]), max_minutes=int(digits[1]))
    if digits:
        v = int(digits[0])
        return Playtime(min_minutes=v, max_minutes=v)
    return Playtime()


def combine_playtimes(a: Playtime, b: Playtime) -> Playtime:
    mins = [x for x in (a.min_minutes, b.min_minutes) if x is not None]
    maxs = [x for x in (a.max_minutes, b.max_minutes) if x is not None]
    return Playtime(min(mins) if mins else None, max(maxs) if maxs else None)


def playtime_overlap(a: Playtime, b: Playtime) -> bool:
    a_hi = a.max_minutes or a.min_minutes or 9999
    b_hi = b.max_minutes or b.min_minutes or 9999
    a_lo = a.min_minutes or 0
    b_lo = b.min_minutes or 0
    return not (a_hi < b_lo or b_hi < a_lo)
