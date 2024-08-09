"""Input validation for models and CLI."""
from __future__ import annotations

import re
from typing import Optional

from .errors import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def require_non_empty(value: str, field: str) -> str:
    v = value.strip()
    if not v:
        raise ValidationError(f"{field} cannot be empty")
    return v


def validate_email(email: str) -> str:
    e = email.strip()
    if e and not _EMAIL_RE.match(e):
        raise ValidationError("invalid email: %s" % e)
    return e


def validate_rating(rating: Optional[float]) -> Optional[float]:
    if rating is None:
        return None
    if rating < 0 or rating > 10:
        raise ValidationError("rating must be 0-10")
    return round(rating, 2)


def validate_player_count(count: int) -> int:
    if count < 1 or count > 100:
        raise ValidationError("player count out of range")
    return count


def validate_minutes(minutes: Optional[int]) -> Optional[int]:
    if minutes is None:
        return None
    if minutes < 1 or minutes > 24 * 60:
        raise ValidationError("duration minutes unrealistic")
    return minutes


def validate_bgg_id(bgg_id: Optional[int]) -> Optional[int]:
    if bgg_id is None:
        return None
    if bgg_id < 1:
        raise ValidationError("bgg id must be positive")
    return bgg_id


def validate_year(year: Optional[int]) -> Optional[int]:
    if year is None:
        return None
    if year < 1900 or year > 2100:
        raise ValidationError("year out of range")
    return year


def parse_int_list(text: str) -> list[int]:
    out = []
    for part in text.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(part))
        except ValueError as exc:
            raise ValidationError(f"not an integer: {part}") from exc
    return out


def validate_title(title: str) -> str:
    return require_non_empty(title, "title")


def validate_port(port: int) -> int:
    if port < 1 or port > 65535:
        raise ValidationError("port out of range")
    return port


def validate_weekday(day: str) -> str:
    d = day.strip().lower()[:3]
    from .recurring import WEEKDAYS

    if d not in WEEKDAYS:
        raise ValidationError("invalid weekday: %s" % day)
    return d


def validate_time_hhmm(text: str) -> str:
    text = text.strip()
    if len(text) == 5 and text[2] == ":":
        hh, mm = text.split(":")
        if hh.isdigit() and mm.isdigit() and 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59:
            return text
    raise ValidationError("time must be HH:MM")


def validate_schema_version(version: int) -> int:
    from .migrate import CURRENT_SCHEMA

    if version < 0 or version > CURRENT_SCHEMA:
        raise ValidationError("schema version invalid")
    return version


def validate_non_negative(value: float, field: str) -> float:
    if value < 0:
        raise ValidationError(f"{field} must be non-negative")
    return value


def sanitize_notes(text: str, max_len: int = 4000) -> str:
    return text.strip()[:max_len]


def validate_collection_name(name: str) -> str:
    n = require_non_empty(name, "collection name")
    if len(n) > 120:
        raise ValidationError("collection name too long")
    return n


def validate_play(play) -> list[str]:
    issues = []
    if not play.game_id:
        issues.append("missing game_id")
    if not play.played_at:
        issues.append("missing played_at")
    if play.duration_minutes is not None:
        try:
            validate_minutes(play.duration_minutes)
        except ValidationError as exc:
            issues.append(str(exc))
    return issues


def validate_game(game) -> list[str]:
    issues = []
    try:
        validate_title(game.title)
    except ValidationError as exc:
        issues.append(str(exc))
    try:
        validate_bgg_id(game.bgg_id)
    except ValidationError as exc:
        issues.append(str(exc))
    try:
        validate_year(game.year)
    except ValidationError as exc:
        issues.append(str(exc))
    return issues
