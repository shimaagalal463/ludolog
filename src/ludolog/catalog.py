"""Catalog maintenance — dedupe, merge, wishlist."""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Tuple

from .game import find_game_by_bgg, find_game_by_title

if TYPE_CHECKING:
    from .game import Game
    from .storage import Library


def duplicate_groups(lib: "Library") -> List[List["Game"]]:
    by_title: Dict[str, List[Game]] = {}
    for g in lib.games:
        key = g.title.strip().lower()
        by_title.setdefault(key, []).append(g)
    return [grp for grp in by_title.values() if len(grp) > 1]


def dedupe_by_title(lib: "Library") -> int:
    merged = 0
    for group in duplicate_groups(lib):
        group.sort(key=lambda g: (g.bgg_id is None, -len(g.mechanics), g.id))
        keeper = group[0]
        for dup in group[1:]:
            keeper.merge_from(dup)
            lib.games.remove(dup)
            merged += 1
            for play in lib.plays:
                if play.game_id == dup.id:
                    play.game_id = keeper.id
    return merged


def wishlist_games(lib: "Library") -> List["Game"]:
    return [g for g in lib.games if g.wishlist and not g.owned]


def owned_games(lib: "Library") -> List["Game"]:
    return [g for g in lib.games if g.owned]


def catalog_stats(lib: "Library") -> Tuple[int, int, int]:
    owned = sum(1 for g in lib.games if g.owned)
    wish = sum(1 for g in lib.games if g.wishlist)
    total = len(lib.games)
    return total, owned, wish


def link_bgg(lib: "Library", game_id: int, bgg_id: int) -> None:
    game = lib.get_game(game_id)
    other = find_game_by_bgg(lib.games, bgg_id)
    if other and other.id != game.id:
        game.merge_from(other)
        lib.games.remove(other)
        for play in lib.plays:
            if play.game_id == other.id:
                play.game_id = game.id
    game.bgg_id = bgg_id


def find_or_create_by_title(lib: "Library", title: str) -> "Game":
    from .game import Game

    existing = find_game_by_title(lib.games, title)
    if existing:
        return existing
    g = Game(title=title)
    return lib.add_game(g)

# FIXME: handle subtitle variants like "Ark Nova (2022)"


def export_wishlist_titles(lib: "Library") -> List[str]:
    return sorted(g.title for g in wishlist_games(lib))


def move_game_to_shelf(lib: "Library", game_id: int, shelf_id: int) -> None:
    from .storage import attach_game_to_shelf

    attach_game_to_shelf(lib, game_id, shelf_id)


def split_by_owned(lib: "Library") -> Tuple[List["Game"], List["Game"]]:
    owned = owned_games(lib)
    other = [g for g in lib.games if not g.owned]
    return owned, other


def bgg_ids_in_catalog(lib: "Library") -> List[int]:
    return [g.bgg_id for g in lib.games if g.bgg_id is not None]


def missing_bgg_ids(lib: "Library") -> List["Game"]:
    return [g for g in lib.games if g.bgg_id is None and g.owned]


def sort_by_rating(lib: "Library", descending: bool = True) -> List["Game"]:
    rated = [g for g in lib.games if g.rating is not None]
    return sorted(rated, key=lambda g: g.rating or 0, reverse=descending)


def apply_bulk_tags(lib: "Library", game_ids: List[int], tag: str) -> int:
    n = 0
    for gid in game_ids:
        g = lib.get_game(gid)
        before = set(g.tags)
        g.add_tag(tag)
        if tag.strip().lower() not in before:
            n += 1
    return n


def prune_orphan_wishlist(lib: "Library") -> int:
    """Remove wishlist-only duplicates that match owned title."""
    removed = 0
    owned_titles = {g.title.lower() for g in lib.games if g.owned}
    keep = []
    for g in lib.games:
        if g.wishlist and not g.owned and g.title.lower() in owned_titles:
            removed += 1
            continue
        keep.append(g)
    lib.games = keep
    return removed
