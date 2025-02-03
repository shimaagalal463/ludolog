"""Aggregate statistics."""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import TYPE_CHECKING, Dict, List, Tuple

from .game import Game
from .play import Play
from .scoreboard import aggregate_wins, player_participation, win_rate

if TYPE_CHECKING:
    from .storage import Library


def play_counts_by_game(plays: List[Play]) -> Counter:
    c: Counter = Counter()
    for p in plays:
        if not p.incomplete:
            c[p.game_id] += 1
    return c


def most_played(lib: "Library", top: int = 10) -> List[Tuple[Game, int]]:
    counts = play_counts_by_game(lib.plays)
    games = {g.id: g for g in lib.games}
    ranked = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    out = []
    for gid, cnt in ranked[:top]:
        g = games.get(gid)
        if g:
            out.append((g, cnt))
    return out


def player_win_rates(lib: "Library") -> List[Tuple[str, float, int]]:
    wins = aggregate_wins(lib.plays)
    rows = []
    for p in lib.players:
        played = player_participation(lib.plays, p.id)
        w = wins.get(p.id, 0)
        rate = win_rate(w, played)
        if played and rate is not None:
            rows.append((p.display_name(), rate, played))
    rows.sort(key=lambda x: (-x[1], -x[2]))
    return rows


def games_for_slot(
    lib: "Library",
    minutes: int,
    players: int,
    slack: int = 0,
    owned_only: bool = True,
) -> List[Game]:
    out = []
    for g in lib.games:
        if owned_only and not g.owned:
            continue
        if g.fits_players(players) and g.fits_minutes(minutes, slack=slack):
            out.append(g)
    out.sort(key=lambda g: (g.playtime.max_minutes or 9999, g.title.lower()))
    return out


def mechanic_frequency(lib: "Library") -> List[Tuple[str, int]]:
    c: Counter = Counter()
    for g in lib.games:
        for m in g.mechanics:
            c[m] += 1
    return c.most_common()


def never_played(lib: "Library") -> List[Game]:
    played_ids = {p.game_id for p in lib.plays if not p.incomplete}
    return [g for g in lib.games if g.owned and g.id not in played_ids]


def average_duration_by_game(plays: List[Play]) -> Dict[int, float]:
    totals: Dict[int, int] = defaultdict(int)
    counts: Dict[int, int] = defaultdict(int)
    for p in plays:
        if p.duration_minutes and not p.incomplete:
            totals[p.game_id] += p.duration_minutes
            counts[p.game_id] += 1
    return {gid: totals[gid] / counts[gid] for gid in totals if counts[gid]}


def update_goal_progress(lib: "Library") -> None:
    from .goal import GoalKind

    wins = aggregate_wins(lib.plays)
    counts = play_counts_by_game(lib.plays)
    for goal in lib.goals:
        if goal.completed:
            continue
        if goal.kind == GoalKind.PLAY_COUNT.value and goal.game_id:
            goal.progress = float(counts.get(goal.game_id, 0))
        elif goal.kind == GoalKind.WIN_RATE.value and goal.player_id:
            played = player_participation(lib.plays, goal.player_id)
            w = wins.get(goal.player_id, 0)
            rate = win_rate(w, played) or 0.0
            goal.progress = rate * 100.0
        elif goal.kind == GoalKind.NEW_GAMES.value:
            played_ids = {p.game_id for p in lib.plays}
            goal.progress = float(len(played_ids))
        goal.refresh_completion()


def plays_per_month(lib: "Library") -> List[Tuple[str, int]]:
    from collections import Counter

    c: Counter = Counter()
    for p in lib.plays:
        if p.incomplete:
            continue
        month = p.played_date()[:7]
        c[month] += 1
    return sorted(c.items())


def average_players_per_session(lib: "Library") -> float:
    if not lib.plays:
        return 0.0
    total = sum(p.player_count() for p in lib.plays if not p.incomplete)
    count = sum(1 for p in lib.plays if not p.incomplete)
    return total / count if count else 0.0


def total_play_minutes(lib: "Library") -> int:
    return sum(p.duration_minutes or 0 for p in lib.plays if p.duration_minutes)


def games_by_designer(lib: "Library") -> List[Tuple[str, int]]:
    from collections import Counter

    c: Counter = Counter()
    for g in lib.games:
        if g.designer:
            c[g.designer] += 1
    return c.most_common()


def h_index_games(plays: List[Play]) -> int:
    """H-index style: h games played at least h times."""
    counts = sorted(play_counts_by_game(plays).values(), reverse=True)
    h = 0
    for i, cnt in enumerate(counts, start=1):
        if cnt >= i:
            h = i
    return h


def player_favorite_game(lib: "Library", player_id: int) -> Tuple[Game | None, int]:
    from collections import Counter

    c: Counter = Counter()
    for p in lib.plays:
        if player_id in p.player_ids and not p.incomplete:
            c[p.game_id] += 1
    if not c:
        return None, 0
    gid, cnt = c.most_common(1)[0]
    game = next((g for g in lib.games if g.id == gid), None)
    return game, cnt


def win_streak(lib: "Library", player_id: int) -> int:
    from .play import sort_plays_newest

    streak = 0
    for play in sort_plays_newest(lib.plays):
        if player_id not in play.player_ids or play.incomplete:
            continue
        if player_id in play.winner_ids:
            streak += 1
        else:
            break
    return streak


def mechanic_play_counts(lib: "Library") -> List[Tuple[str, int]]:
    from collections import Counter

    c: Counter = Counter()
    games = {g.id: g for g in lib.games}
    for play in lib.plays:
        if play.incomplete:
            continue
        g = games.get(play.game_id)
        if not g:
            continue
        for m in g.mechanics:
            c[m] += 1
    return c.most_common()


def collection_value_estimate(lib: "Library", default_price: float = 40.0) -> float:
    """Rough shelf value — flat default unless game has rating-based bump."""
    total = 0.0
    for g in lib.games:
        if not g.owned:
            continue
        bump = (g.rating or 0) * 2.0
        total += default_price + bump
    return total


def compare_player_win_rates(lib: "Library", a_id: int, b_id: int) -> Tuple[float, float]:
    wins = aggregate_wins(lib.plays)
    def rate(pid: int) -> float:
        played = player_participation(lib.plays, pid)
        w = wins.get(pid, 0)
        return win_rate(w, played) or 0.0
    return rate(a_id), rate(b_id)


def head_to_head(lib: "Library", a_id: int, b_id: int) -> Tuple[int, int, int]:
    """Wins for a, wins for b, ties (both win or neither)."""
    aw = bw = ties = 0
    for play in lib.plays:
        if play.incomplete:
            continue
        if a_id not in play.player_ids or b_id not in play.player_ids:
            continue
        a_won = a_id in play.winner_ids
        b_won = b_id in play.winner_ids
        if a_won and not b_won:
            aw += 1
        elif b_won and not a_won:
            bw += 1
        else:
            ties += 1
    return aw, bw, ties


def leaderboard(lib: "Library", top: int = 10) -> List[Tuple[str, int, int]]:
    wins = aggregate_wins(lib.plays)
    rows = []
    for p in lib.players:
        played = player_participation(lib.plays, p.id)
        rows.append((p.display_name(), wins.get(p.id, 0), played))
    rows.sort(key=lambda x: (-x[1], -x[2]))
    return rows[:top]


def monthly_unique_games(lib: "Library") -> List[Tuple[str, int]]:
    from collections import defaultdict
    buckets: dict[str, set[int]] = defaultdict(set)
    for p in lib.plays:
        if p.incomplete:
            continue
        buckets[p.played_date()[:7]].add(p.game_id)
    return sorted((m, len(s)) for m, s in buckets.items())


def player_activity_matrix(lib: "Library") -> dict[int, dict[int, int]]:
    matrix: dict[int, dict[int, int]] = {}
    for play in lib.plays:
        if play.incomplete:
            continue
        row = matrix.setdefault(play.game_id, {})
        for pid in play.player_ids:
            row[pid] = row.get(pid, 0) + 1
    return matrix


def dormant_games(lib: "Library", days: int = 90) -> List[Game]:
    from .play import days_since_last_play
    out = []
    for g in lib.games:
        if not g.owned:
            continue
        gap = days_since_last_play(lib.plays, g.id)
        if gap is None or gap >= days:
            out.append(g)
    return sorted(out, key=lambda g: g.title.lower())


def venue_leaderboard(lib: "Library", top: int = 5) -> List[Tuple[str, int]]:
    from .venue import venue_play_counts
    return venue_play_counts(lib)[:top]


def shelf_fill_rates(lib: "Library") -> List[Tuple[str, float]]:
    rows = []
    for shelf in lib.shelves:
        count = len([g for g in lib.games if g.shelf_id == shelf.id])
        if shelf.capacity:
            rows.append((shelf.name, count / shelf.capacity))
    return sorted(rows, key=lambda x: -x[1])


def rating_histogram(lib: "Library") -> List[Tuple[int, int]]:
    from collections import Counter
    c: Counter = Counter()
    for g in lib.games:
        if g.rating is not None:
            bucket = int(g.rating)
            c[bucket] += 1
    return sorted(c.items())


def streak_longest_win(lib: "Library", player_id: int) -> int:
    from .play import sort_plays_newest
    best = cur = 0
    for play in reversed(sort_plays_newest(lib.plays)):
        if player_id not in play.player_ids or play.incomplete:
            continue
        if player_id in play.winner_ids:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def compare_mechanics(lib: "Library", mech_a: str, mech_b: str) -> Tuple[int, int]:
    from .game import games_by_mechanic
    return len(games_by_mechanic(lib.games, mech_a)), len(games_by_mechanic(lib.games, mech_b))


def estimate_nights_to_clear_backlog(lib: "Library", games_per_night: float = 1.5) -> float:
    backlog = len(never_played(lib))
    if backlog == 0:
        return 0.0
    return backlog / games_per_night


def player_attendance_rate(lib: "Library", player_id: int) -> float:
    if not lib.plays:
        return 0.0
    attended = player_participation(lib.plays, player_id)
    return attended / len(lib.plays)


def summary_numbers(lib: "Library") -> dict:
    return {
        "games": len(lib.games),
        "plays": len(lib.plays),
        "players": len(lib.players),
        "avg_players": average_players_per_session(lib),
        "minutes": total_play_minutes(lib),
    }


def top_designers_by_plays(lib: "Library", top: int = 5) -> list[tuple[str, int]]:
    from collections import Counter
    games = {g.id: g for g in lib.games}
    c: Counter = Counter()
    for p in lib.plays:
        g = games.get(p.game_id)
        if g and g.designer:
            c[g.designer] += 1
    return c.most_common(top)


def plays_by_weekday(lib: "Library") -> list[tuple[str, int]]:
    from collections import Counter
    from datetime import datetime
    c: Counter = Counter()
    for p in lib.plays:
        try:
            wd = datetime.fromisoformat(p.played_at.replace("Z", "")).strftime("%a")
        except ValueError:
            wd = "?"
        c[wd] += 1
    order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return [(d, c.get(d, 0)) for d in order]


def coop_rate(lib: "Library") -> float:
    from .scoreboard import coop_sessions
    if not lib.plays:
        return 0.0
    return len(coop_sessions(lib.plays)) / len(lib.plays)


def player_engagement(lib: "Library") -> list[tuple[str, float]]:
    rows = []
    for p in lib.players:
        rate = player_attendance_rate(lib, p.id)
        rows.append((p.display_name(), rate))
    rows.sort(key=lambda x: -x[1])
    return rows


def publisher_diversity(lib: "Library") -> int:
    return len({g.publisher for g in lib.games if g.publisher})


def mechanic_diversity(lib: "Library") -> int:
    return len({m for g in lib.games for m in g.mechanics})


def compute_stats_dashboard(lib: "Library") -> dict:
    return {
        "summary": summary_numbers(lib),
        "mechanic_diversity": mechanic_diversity(lib),
        "publisher_diversity": publisher_diversity(lib),
        "coop_rate": coop_rate(lib),
        "h_index": h_index_games(lib.plays),
        "backlog_nights": estimate_nights_to_clear_backlog(lib),
    }


def format_dashboard(lib: "Library") -> str:
    dash = compute_stats_dashboard(lib)
    lines = ["ludolog dashboard", ""]
    for section, data in dash.items():
        lines.append(section + ":")
        if isinstance(data, dict):
            for k, v in data.items():
                lines.append(f"  {k}: {v}")
        else:
            lines.append(f"  {data}")
        lines.append("")
    return "\n".join(lines)


def game_retention_score(lib: "Library", game_id: int) -> float:
    from .play import first_play, last_play, plays_for_game
    gp = plays_for_game(lib.plays, game_id)
    if len(gp) < 2:
        return 0.0
    fp = first_play(lib.plays, game_id)
    lp = last_play(lib.plays, game_id)
    if not fp or not lp:
        return 0.0
    span = (lp.played_datetime() - fp.played_datetime()).days or 1
    return len(gp) / span
