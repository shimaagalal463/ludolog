"""Parse CLI-friendly field strings."""
from __future__ import annotations

from typing import Dict, List, Tuple

from .player_range import parse_player_range
from .playtime import parse_playtime


def parse_key_values(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for chunk in text.split(","):
        if "=" not in chunk:
            continue
        k, v = chunk.split("=", 1)
        out[k.strip().lower()] = v.strip()
    return out


def parse_score_pairs(text: str) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for chunk in text.split(","):
        if ":" not in chunk:
            continue
        name, val = chunk.split(":", 1)
        try:
            scores[name.strip()] = float(val.strip())
        except ValueError:
            continue
    return scores


def parse_tags(text: str) -> List[str]:
    return [t.strip().lower() for t in text.split(",") if t.strip()]


def parse_game_fields(
    title: str,
    players: str = "",
    minutes: str = "",
    mechanics: str = "",
) -> Tuple[str, object, object, List[str]]:
    mech = [m.strip() for m in mechanics.split(",") if m.strip()]
    return title.strip(), parse_player_range(players), parse_playtime(minutes), mech


def split_names(text: str) -> List[str]:
    return [n.strip() for n in text.replace(";", ",").split(",") if n.strip()]


def parse_duration_arg(text: str) -> int | None:
    text = text.strip().lower()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    if text.endswith("h"):
        try:
            return int(float(text[:-1]) * 60)
        except ValueError:
            return None
    return None


def parse_bool(text: str) -> bool:
    return text.strip().lower() in ("1", "true", "yes", "y", "on")
