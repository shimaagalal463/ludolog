"""Play scoring and rankings."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .play import Play
from .player import Player


def rank_by_scores(play: Play) -> List[Tuple[int, float]]:
    items = [(int(pid), score) for pid, score in play.scores.items()]
    return sorted(items, key=lambda x: (-x[1], x[0]))


def winner_names(play: Play, players: List[Player]) -> List[str]:
    by_id = {p.id: p for p in players}
    names = []
    for wid in play.winner_ids:
        p = by_id.get(wid)
        names.append(p.display_name() if p else f"#{wid}")
    return names


def scoreboard_lines(play: Play, players: List[Player]) -> List[str]:
    by_id = {p.id: p for p in players}
    lines = []
    for pid, score in rank_by_scores(play):
        p = by_id.get(pid)
        label = p.display_name() if p else f"player {pid}"
        marker = "*" if pid in play.winner_ids else " "
        lines.append(f"{marker} {label}: {score:g}")
    return lines


def aggregate_wins(plays: List[Play]) -> Dict[int, int]:
    wins: Dict[int, int] = {}
    for play in plays:
        if play.incomplete:
            continue
        for wid in play.winner_ids:
            wins[wid] = wins.get(wid, 0) + 1
    return wins


def win_rate(wins: int, games_played: int) -> Optional[float]:
    if games_played <= 0:
        return None
    return wins / games_played


def player_participation(plays: List[Play], player_id: int) -> int:
    count = 0
    for p in plays:
        if player_id in p.player_ids:
            count += 1
    return count


def coop_sessions(plays: List[Play]) -> List[Play]:
    return [p for p in plays if p.is_coop_win()]

# FIXME: some games use low-score-wins — need per-game scoring direction


def lowest_scorers(play: Play) -> List[int]:
    if not play.scores:
        return []
    worst = min(play.scores.values())
    return [int(pid) for pid, val in play.scores.items() if val == worst]


def score_spread(play: Play) -> float | None:
    if len(play.scores) < 2:
        return None
    vals = list(play.scores.values())
    return max(vals) - min(vals)


def per_player_average(plays: List[Play], player_id: int) -> float | None:
    scores = [p.get_score(player_id) for p in plays if p.get_score(player_id) is not None]
    if not scores:
        return None
    return sum(scores) / len(scores)


def format_leaderboard(rows: List[tuple[str, float, int]]) -> str:
    lines = []
    for name, rate, played in rows:
        lines.append(f"{name}: {rate:.1%} ({played} games)")
    return "\n".join(lines)


def build_standings(plays, players, game_id: int | None = None) -> list[tuple[str, int, int]]:
    from .play import plays_for_game
    subset = plays_for_game(plays, game_id) if game_id else plays
    wins = aggregate_wins(subset)
    rows = []
    for p in players:
        played = player_participation(subset, p.id)
        if played:
            rows.append((p.display_name(), wins.get(p.id, 0), played))
    rows.sort(key=lambda x: (-x[1], -x[2]))
    return rows


def export_standings_text(plays, players) -> str:
    return format_leaderboard([(n, w / p if p else 0, p) for n, w, p in build_standings(plays, players)])
