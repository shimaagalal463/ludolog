"""CSV import/export."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .errors import ImportError as LudologImportError
from .game import Game
from .parser import parse_game_fields, split_names
from .play import Play
from .player import Player, find_player_by_name

if TYPE_CHECKING:
    from .storage import Library


def export_plays_csv(lib: "Library", path: Path | str) -> int:
    p = Path(path)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["played_at", "game_title", "players", "winners", "duration", "notes"])
        games = {g.id: g for g in lib.games}
        players = {pl.id: pl for pl in lib.players}
        for play in lib.plays:
            title = games.get(play.game_id)
            t = title.title if title else str(play.game_id)
            pnames = ",".join(players[i].display_name() for i in play.player_ids if i in players)
            wnames = ",".join(players[i].display_name() for i in play.winner_ids if i in players)
            w.writerow([
                play.played_at,
                t,
                pnames,
                wnames,
                play.duration_minutes or "",
                play.notes,
            ])
    return len(lib.plays)


def import_plays_csv(lib: "Library", path: Path | str) -> int:
    p = Path(path)
    if not p.exists():
        raise LudologImportError("csv not found: %s" % p)
    count = 0
    with p.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            title = (row.get("game_title") or row.get("game") or "").strip()
            if not title:
                continue
            game = _ensure_game(lib, title)
            player_names = split_names(row.get("players") or "")
            winner_names = split_names(row.get("winners") or "")
            pids = _ensure_players(lib, player_names)
            wids = []
            for w in winner_names:
                pl = find_player_by_name(lib.players, w)
                if pl:
                    wids.append(pl.id)
            played_at = row.get("played_at") or datetime.now().isoformat(timespec="seconds")
            dur = row.get("duration") or row.get("duration_minutes")
            duration = int(dur) if dur and str(dur).isdigit() else None
            play = Play(
                game_id=game.id,
                played_at=played_at,
                player_ids=pids,
                winner_ids=wids,
                duration_minutes=duration,
                notes=row.get("notes") or "",
            )
            lib.add_play(play)
            count += 1
    return count


def export_games_csv(lib: "Library", path: Path | str) -> int:
    p = Path(path)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["title", "bgg_id", "designer", "players", "minutes", "mechanics", "owned"])
        for g in lib.games:
            w.writerow([
                g.title,
                g.bgg_id or "",
                g.designer,
                g.player_range.label(),
                g.playtime.label(),
                "|".join(g.mechanics),
                "yes" if g.owned else "no",
            ])
    return len(lib.games)


def _ensure_game(lib: "Library", title: str) -> Game:
    from .game import find_game_by_title

    g = find_game_by_title(lib.games, title)
    if g:
        return g
    return lib.add_game(Game(title=title))


def _ensure_players(lib: "Library", names: list[str]) -> list[int]:
    ids = []
    for name in names:
        pl = find_player_by_name(lib.players, name)
        if not pl:
            pl = lib.add_player(Player(name=name))
        ids.append(pl.id)
    return ids


def import_games_csv(lib, path) -> int:
    import csv
    from pathlib import Path
    from .game import Game
    from .player_range import PlayerRange
    from .playtime import Playtime
    p = Path(path)
    count = 0
    with p.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            title = (row.get("title") or "").strip()
            if not title:
                continue
            from .game import find_game_by_title
            if find_game_by_title(lib.games, title):
                continue
            pr = PlayerRange()
            pl = row.get("players") or ""
            if "-" in pl:
                a, b = pl.split("-", 1)
                pr = PlayerRange(int(a), int(b))
            pt = Playtime()
            mins = row.get("minutes") or ""
            if "-" in mins:
                a, b = mins.split("-", 1)
                pt = Playtime(int(a), int(b))
            mech = [m.strip() for m in (row.get("mechanics") or "").replace("|", ",").split(",") if m.strip()]
            lib.add_game(Game(title=title, player_range=pr, playtime=pt, mechanics=mech))
            count += 1
    return count


def sniff_csv_dialect(path) -> csv.Dialect:
    import csv
    from pathlib import Path
    sample = Path(path).read_text(encoding="utf-8-sig")[:2048]
    try:
        return csv.Sniffer().sniff(sample)
    except csv.Error:
        return csv.excel


def export_players_csv(lib, path) -> int:
    import csv
    from pathlib import Path
    p = Path(path)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "name", "handle", "email", "active"])
        for pl in lib.players:
            w.writerow([pl.id, pl.name, pl.handle, pl.email, "yes" if pl.active else "no"])
    return len(lib.players)

# FIXME: delimiter autodetect fails on mixed European CSV exports
