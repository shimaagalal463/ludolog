"""Global and per-game tag management."""
from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .storage import Library


def normalize_tag(tag: str) -> str:
    return tag.strip().lower().replace(" ", "-")


def add_global_tag(lib: "Library", tag: str) -> bool:
    t = normalize_tag(tag)
    if not t:
        return False
    if t not in lib.tags:
        lib.tags.append(t)
        return True
    return False


def remove_global_tag(lib: "Library", tag: str) -> bool:
    t = normalize_tag(tag)
    if t in lib.tags:
        lib.tags.remove(t)
        return True
    return False


def all_tags(lib: "Library") -> List[str]:
    seen = set(lib.tags)
    for g in lib.games:
        for t in g.tags:
            seen.add(t)
    return sorted(seen)


def rename_tag(lib: "Library", old: str, new: str) -> int:
    o, n = normalize_tag(old), normalize_tag(new)
    changed = 0
    if o in lib.tags:
        lib.tags.remove(o)
        add_global_tag(lib, n)
    for g in lib.games:
        if o in g.tags:
            g.tags.remove(o)
            g.add_tag(n)
            changed += 1
    return changed


def games_with_tag(lib: "Library", tag: str) -> List[int]:
    t = normalize_tag(tag)
    return [g.id for g in lib.games if t in g.tags or t in [normalize_tag(x) for x in g.tags]]


def tag_cloud(lib) -> List[tuple[str, int]]:
    from collections import Counter
    c: Counter = Counter()
    for t in lib.tags:
        c[normalize_tag(t)] += 1
    for g in lib.games:
        for t in g.tags:
            c[normalize_tag(t)] += 1
    return c.most_common()


def untagged_games(lib) -> list:
    return [g for g in lib.games if not g.tags]


def sync_global_tags_from_games(lib) -> int:
    added = 0
    for g in lib.games:
        for t in g.tags:
            if add_global_tag(lib, t):
                added += 1
    return added
