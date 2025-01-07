"""Text reports for CLI and scripts."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .play import plays_in_range, sort_plays_newest
from .scoreboard import scoreboard_lines, winner_names
from .stats import most_played, never_played, player_win_rates

if TYPE_CHECKING:
    from .storage import Library


def summary_report(lib: "Library") -> str:
    lines = [
        "ludolog summary",
        "games: %d (owned %d)" % (len(lib.games), sum(1 for g in lib.games if g.owned)),
        "plays: %d" % len(lib.plays),
        "players: %d" % len(lib.players),
        "",
        "most played:",
    ]
    for game, cnt in most_played(lib, 5):
        lines.append("  %s — %d" % (game.title, cnt))
    unplayed = never_played(lib)
    if unplayed:
        lines.append("")
        lines.append("never played (%d):" % len(unplayed))
        for g in unplayed[:5]:
            lines.append("  " + g.title)
    return "\n".join(lines)


def game_night_report(lib: "Library", days: int = 7) -> str:
    from datetime import date, timedelta

    end = date.today()
    start = end - timedelta(days=days)
    plays = plays_in_range(lib.plays, start.isoformat(), end.isoformat())
    plays = sort_plays_newest(plays)
    games = {g.id: g for g in lib.games}
    lines = ["game night report (%d days)" % days, "sessions: %d" % len(plays), ""]
    for play in plays:
        g = games.get(play.game_id)
        title = g.title if g else "?"
        winners = winner_names(play, lib.players)
        wtxt = ", ".join(winners) if winners else "—"
        lines.append("%s  %s  winners: %s" % (play.played_date(), title, wtxt))
    return "\n".join(lines)


def player_report(lib: "Library", player_id: int) -> str:
    from .errors import NotFoundError

    player = None
    for p in lib.players:
        if p.id == player_id:
            player = p
            break
    if not player:
        raise NotFoundError("player %d not found" % player_id)
    lines = ["player: %s" % player.display_name(), ""]
    for name, rate, played in player_win_rates(lib):
        if name == player.display_name():
            lines.append(f"win rate: {rate:.1%} over {played} plays")
            break
    lines.append("")
    lines.append("recent plays:")
    for play in sort_plays_newest(lib.plays)[:10]:
        if player_id not in play.player_ids:
            continue
        g = lib.get_game(play.game_id)
        lines.extend(scoreboard_lines(play, lib.players))
        lines.append("")
    return "\n".join(lines).strip()


def shelf_report(lib: "Library", shelf_id: int) -> str:
    shelf = lib.get_shelf(shelf_id)
    on_shelf = [g for g in lib.games if g.shelf_id == shelf_id]
    lines = [
        f"shelf: {shelf.room_label()}",
        f"games: {len(on_shelf)}",
    ]
    if shelf.capacity:
        lines.append(f"capacity: {shelf.capacity} ({len(on_shelf)}/{shelf.capacity})")
    for g in sorted(on_shelf, key=lambda x: x.title.lower()):
        lines.append("  " + g.title)
    return "\n".join(lines)


def season_report(lib: "Library", season_id: int) -> str:
    season = next((s for s in lib.seasons if s.id == season_id), None)
    if not season:
        from .errors import NotFoundError
        raise NotFoundError("season %d not found" % season_id)
    plays = [p for p in lib.plays if season.contains_date(p.played_date())]
    games = {g.id: g for g in lib.games}
    lines = [f"season: {season.name}", f"plays: {len(plays)}", ""]
    from .stats import play_counts_by_game
    counts = play_counts_by_game(plays)
    for gid, cnt in sorted(counts.items(), key=lambda x: -x[1])[:10]:
        g = games.get(gid)
        lines.append(f"  {g.title if g else gid}: {cnt}")
    return "\n".join(lines)


def mechanic_report(lib: "Library", mechanic: str) -> str:
    from .game import games_by_mechanic
    from .search import games_by_mechanic as ids_by_mech

    gids = set(ids_by_mech(lib, mechanic))
    titles = [g.title for g in games_by_mechanic(lib.games, mechanic)]
    play_count = sum(1 for p in lib.plays if p.game_id in gids and not p.incomplete)
    lines = [f"mechanic: {mechanic}", f"owned: {len(titles)}", f"plays logged: {play_count}", ""]
    for t in sorted(titles)[:20]:
        lines.append("  " + t)
    return "\n".join(lines)


def venue_report(lib: "Library", venue_id: int) -> str:
    from .storage import plays_at_venue

    venue = lib.get_venue(venue_id)
    plays = plays_at_venue(lib, venue_id)
    games = {g.id: g for g in lib.games}
    lines = [f"venue: {venue.name}", f"sessions: {len(plays)}", ""]
    for play in sort_plays_newest(plays)[:15]:
        g = games.get(play.game_id)
        lines.append(format_play_line(play, g.title if g else "?"))
    return "\n".join(lines)


def format_play_line(play, title: str) -> str:
    return "%s  %s  %dp" % (play.played_date(), title, play.player_count())


def collection_report(lib: "Library", collection_id: int) -> str:
    coll = next((c for c in lib.collections if c.id == collection_id), None)
    if not coll:
        from .errors import NotFoundError
        raise NotFoundError("collection %d not found" % collection_id)
    games = {g.id: g for g in lib.games}
    lines = [f"collection: {coll.name}", coll.description, ""]
    for gid in coll.game_ids:
        g = games.get(gid)
        if g:
            lines.append(f"  {g.title} ({g.player_label()})")
    return "\n".join(lines)


def goals_report(lib: "Library") -> str:
    from .goal import open_goals
    from .stats import update_goal_progress

    update_goal_progress(lib)
    lines = ["open goals:", ""]
    for g in open_goals(lib.goals):
        lines.append(f"  [{g.pct():.0f}%] {g.title} ({g.progress:g}/{g.target:g})")
    if len(lines) == 2:
        lines.append("  (none)")
    return "\n".join(lines)


def recurring_report(lib: "Library") -> str:
    from .recurring import active_nights

    lines = ["recurring game nights:", ""]
    for n in active_nights(lib.recurring_nights):
        venue = None
        if n.default_venue_id:
            try:
                venue = lib.get_venue(n.default_venue_id)
            except Exception:
                venue = None
        vname = venue.name if venue else "—"
        lines.append(f"  {n.weekday_label()} {n.start_time} — {n.name} @ {vname}")
    return "\n".join(lines)


def full_report(lib: "Library") -> str:
    chunks = [summary_report(lib), "", goals_report(lib), "", recurring_report(lib)]
    return "\n\n".join(chunks)


def compare_players_report(lib: "Library", a_id: int, b_id: int) -> str:
    from .stats import compare_player_win_rates, head_to_head
    pa = lib.get_player(a_id).display_name()
    pb = lib.get_player(b_id).display_name()
    ra, rb = compare_player_win_rates(lib, a_id, b_id)
    aw, bw, ties = head_to_head(lib, a_id, b_id)
    return "\n".join([
        f"{pa} vs {pb}",
        f"win rates: {ra:.1%} vs {rb:.1%}",
        f"head-to-head: {aw}-{bw} (ties {ties})",
    ])


def backlog_report(lib: "Library") -> str:
    from .stats import never_played
    games = never_played(lib)
    lines = [f"unplayed owned: {len(games)}", ""]
    for g in games[:25]:
        lines.append(f"  {g.title} ({g.playtime_label()})")
    return "\n".join(lines)
