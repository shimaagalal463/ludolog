"""BG Stats play history import."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .catalog import find_or_create_by_title
from .errors import ImportError as LudologImportError
from .game import find_game_by_title
from .parser import split_names
from .play import Play
from .player import Player, find_player_by_name

if TYPE_CHECKING:
    from .storage import Library


def import_bgstats_csv(lib: "Library", path: Path | str) -> int:
    p = Path(path)
    if not p.exists():
        raise LudologImportError("bg stats csv not found: %s" % p)
    count = 0
    with p.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            title = (row.get("Game") or row.get("game") or row.get("Title") or "").strip()
            if not title:
                continue
            game = find_game_by_title(lib.games, title)
            if not game:
                game = find_or_create_by_title(lib, title)
            players_raw = row.get("Players") or row.get("players") or ""
            winners_raw = row.get("Winner") or row.get("Winners") or row.get("winner") or ""
            pids = _resolve_players(lib, split_names(players_raw))
            wids = _resolve_winners(lib, winners_raw, pids)
            played = _parse_bgstats_date(row.get("Date") or row.get("date") or "")
            duration = _parse_duration(row.get("Duration") or row.get("Play Time") or "")
            location = (row.get("Location") or "").strip()
            venue_id = _match_venue(lib, location)
            play = Play(
                game_id=game.id,
                played_at=played,
                player_ids=pids,
                winner_ids=wids,
                duration_minutes=duration,
                venue_id=venue_id,
                notes=row.get("Comments") or row.get("Notes") or "",
            )
            lib.add_play(play)
            count += 1
    return count


def _resolve_players(lib: "Library", names: list[str]) -> list[int]:
    ids = []
    for name in names:
        pl = find_player_by_name(lib.players, name)
        if not pl:
            pl = lib.add_player(Player(name=name))
        ids.append(pl.id)
    return ids


def _resolve_winners(lib: "Library", winners_raw: str, seated: list[int]) -> list[int]:
    if not winners_raw.strip():
        return []
    if winners_raw.strip().lower() in ("all", "cooperative win", "team win"):
        return list(seated)
    names = split_names(winners_raw)
    wids = []
    for name in names:
        pl = find_player_by_name(lib.players, name)
        if pl:
            wids.append(pl.id)
    return wids


def _parse_bgstats_date(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return datetime.now().isoformat(timespec="seconds")
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).isoformat(timespec="seconds")
        except ValueError:
            continue
    return raw


def _parse_duration(raw: str) -> int | None:
    raw = raw.strip().lower()
    if not raw:
        return None
    if raw.isdigit():
        return int(raw)
    if "h" in raw:
        parts = raw.replace("min", "").replace("m", "").split("h")
        try:
            hours = int(parts[0].strip() or 0)
            mins = int(parts[1].strip() or 0) if len(parts) > 1 else 0
            return hours * 60 + mins
        except ValueError:
            return None
    digits = "".join(c if c.isdigit() else " " for c in raw).split()
    if digits:
        return int(digits[0])
    return None


def _match_venue(lib: "Library", location: str) -> int | None:
    if not location:
        return None
    needle = location.lower()
    for v in lib.venues:
        if v.name.lower() == needle:
            return v.id
    from .venue import Venue

    return lib.add_venue(Venue(name=location)).id


def plays_to_bgstats_rows(lib) -> list[dict[str, str]]:
    games = {g.id: g for g in lib.games}
    players = {p.id: p for p in lib.players}
    rows = []
    for play in lib.plays:
        g = games.get(play.game_id)
        pnames = ",".join(players[i].name for i in play.player_ids if i in players)
        wnames = ",".join(players[i].name for i in play.winner_ids if i in players)
        rows.append({
            "Game": g.title if g else str(play.game_id),
            "Date": play.played_date(),
            "Players": pnames,
            "Winner": wnames,
            "Duration": str(play.duration_minutes or ""),
        })
    return rows


def detect_bgstats_columns(header: list[str]) -> dict[str, str]:
    mapping = {}
    lower = {h.lower(): h for h in header}
    for want in ("game", "date", "players", "winner", "duration", "location"):
        for h in header:
            if want in h.lower():
                mapping[want] = h
                break
    return mapping


def import_bgstats_flexible(lib, path) -> int:
    import csv
    from pathlib import Path
    p = Path(path)
    count = 0
    with p.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        cols = detect_bgstats_columns(reader.fieldnames or [])
        for row in reader:
            title = row.get(cols.get("game", "Game"), "").strip()
            if not title:
                continue
            from .catalog import find_or_create_by_title
            from .game import find_game_by_title
            game = find_game_by_title(lib.games, title) or find_or_create_by_title(lib, title)
            players_raw = row.get(cols.get("players", "Players"), "")
            winners_raw = row.get(cols.get("winner", "Winner"), "")
            from .parser import split_names
            pids = _resolve_players(lib, split_names(players_raw))
            wids = _resolve_winners(lib, winners_raw, pids)
            played = _parse_bgstats_date(row.get(cols.get("date", "Date"), ""))
            duration = _parse_duration(row.get(cols.get("duration", "Duration"), ""))
            location = row.get(cols.get("location", "Location"), "")
            from .play import Play
            play = Play(
                game_id=game.id,
                played_at=played,
                player_ids=pids,
                winner_ids=wids,
                duration_minutes=duration,
                venue_id=_match_venue(lib, location),
            )
            lib.add_play(play)
            count += 1
    return count
