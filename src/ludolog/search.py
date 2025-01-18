"""Search across games, players, and plays."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from .mechanics import mechanic_overlap

if TYPE_CHECKING:
    from .storage import Library


@dataclass
class SearchHit:
    kind: str
    score: float
    label: str
    ref_id: int


def _score_substring(needle: str, hay: str) -> float:
    n, h = needle.lower(), hay.lower()
    if not n or not h:
        return 0.0
    if n == h:
        return 100.0
    if h.startswith(n):
        return 80.0
    if n in h:
        return 50.0 + min(20.0, 20.0 * len(n) / max(len(h), 1))
    return 0.0


def search_games(lib: "Library", query: str, limit: int = 20) -> List[SearchHit]:
    hits: List[SearchHit] = []
    for g in lib.games:
        score = max(
            _score_substring(query, g.title),
            _score_substring(query, g.designer),
            _score_substring(query, g.publisher),
        )
        for tag in g.tags:
            score = max(score, _score_substring(query, tag) * 0.8)
        for mech in g.mechanics:
            score = max(score, _score_substring(query, mech) * 0.7)
        if score > 0:
            hits.append(SearchHit("game", score, g.title, g.id))
    hits.sort(key=lambda h: (-h.score, h.label.lower()))
    return hits[:limit]


def search_players(lib: "Library", query: str, limit: int = 20) -> List[SearchHit]:
    hits = []
    for p in lib.players:
        score = max(_score_substring(query, p.name), _score_substring(query, p.handle))
        if score > 0:
            hits.append(SearchHit("player", score, p.display_name(), p.id))
    hits.sort(key=lambda h: (-h.score, h.label.lower()))
    return hits[:limit]


def search_all(lib: "Library", query: str, limit: int = 30) -> List[SearchHit]:
    combined = search_games(lib, query, limit) + search_players(lib, query, limit)
    combined.sort(key=lambda h: (-h.score, h.kind, h.label.lower()))
    return combined[:limit]


def games_by_mechanic(lib: "Library", mechanic: str) -> List[int]:
    from .mechanics import normalize_mechanic

    m = normalize_mechanic(mechanic)
    return [g.id for g in lib.games if m in g.mechanics]


def similar_games(lib: "Library", game_id: int, limit: int = 5) -> List[SearchHit]:
    base = lib.get_game(game_id)
    hits: List[SearchHit] = []
    for g in lib.games:
        if g.id == game_id:
            continue
        overlap = mechanic_overlap(base.mechanics, g.mechanics)
        score = 10.0 * len(overlap)
        if base.designer and base.designer.lower() == g.designer.lower():
            score += 15.0
        pr_match = base.player_range.min_players == g.player_range.min_players
        if pr_match:
            score += 5.0
        if score > 0:
            hits.append(SearchHit("game", score, g.title, g.id))
    hits.sort(key=lambda h: (-h.score, h.label.lower()))
    return hits[:limit]

# TODO: index by inverted mechanic map for huge collections


def search_by_designer(lib: "Library", designer: str, limit: int = 20) -> List[SearchHit]:
    hits = []
    for g in lib.games:
        score = _score_substring(designer, g.designer)
        if score > 0:
            hits.append(SearchHit("game", score, g.title, g.id))
    hits.sort(key=lambda h: (-h.score, h.label.lower()))
    return hits[:limit]


def search_by_tag(lib: "Library", tag: str, limit: int = 50) -> List[SearchHit]:
    from .tags_manager import normalize_tag

    t = normalize_tag(tag)
    hits = []
    for g in lib.games:
        if t in [normalize_tag(x) for x in g.tags]:
            hits.append(SearchHit("game", 100.0, g.title, g.id))
    return hits[:limit]


def filter_games(
    lib: "Library",
    *,
    owned: bool | None = None,
    wishlist: bool | None = None,
    mechanic: str = "",
    min_players: int | None = None,
    max_minutes: int | None = None,
) -> List[SearchHit]:
    from .mechanics import normalize_mechanic

    m = normalize_mechanic(mechanic) if mechanic else ""
    hits = []
    for g in lib.games:
        if owned is not None and g.owned != owned:
            continue
        if wishlist is not None and g.wishlist != wishlist:
            continue
        if m and m not in g.mechanics:
            continue
        if min_players is not None and not g.fits_players(min_players):
            continue
        if max_minutes is not None:
            hi = g.playtime.max_minutes if g.playtime.max_minutes is not None else g.playtime.min_minutes
            if hi is not None and hi > max_minutes:
                continue
        hits.append(SearchHit("game", 1.0, g.title, g.id))
    hits.sort(key=lambda h: h.label.lower())
    return hits


def suggest_for_player(lib: "Library", player_id: int, limit: int = 5) -> List[SearchHit]:
    player = lib.get_player(player_id)
    fav = player.favorite_mechanics
    if not fav:
        return []
    scores: dict[int, float] = {}
    for g in lib.games:
        if not g.owned:
            continue
        overlap = mechanic_overlap(fav, g.mechanics)
        if overlap:
            scores[g.id] = 10.0 * len(overlap)
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    hits = []
    games = {g.id: g for g in lib.games}
    for gid, score in ranked[:limit]:
        hits.append(SearchHit("game", score, games[gid].title, gid))
    return hits


def autocomplete_titles(lib: "Library", prefix: str, limit: int = 10) -> List[str]:
    p = prefix.lower()
    hits = []
    for g in lib.games:
        if g.title.lower().startswith(p):
            hits.append(g.title)
    return sorted(hits)[:limit]


def search_notes(lib: "Library", query: str) -> List[SearchHit]:
    from .note import search_notes
    hits = []
    for note in search_notes(lib.notes, query):
        hits.append(SearchHit("note", 50.0, note.body[:60], note.id))
    return hits


def ranked_wishlist(lib: "Library") -> List[SearchHit]:
    from .catalog import wishlist_games
    games = sorted(wishlist_games(lib), key=lambda g: (-(g.rating or 0), g.title.lower()))
    return [SearchHit("game", g.rating or 0, g.title, g.id) for g in games]
