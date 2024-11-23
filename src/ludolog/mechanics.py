"""Board game mechanics taxonomy helpers."""
from __future__ import annotations

from typing import Iterable, List, Set


CANONICAL_MECHANICS = {
    "area control",
    "auction",
    "bluffing",
    "cooperative",
    "deck building",
    "deduction",
    "drafting",
    "engine building",
    "hand management",
    "modular board",
    "negotiation",
    "pattern building",
    "pick-up and deliver",
    "push your luck",
    "set collection",
    "tile placement",
    "trick-taking",
    "worker placement",
}


def normalize_mechanic(raw: str) -> str:
    s = raw.strip().lower().replace("_", " ").replace("-", " ")
    while "  " in s:
        s = s.replace("  ", " ")
    return s


def normalize_mechanics(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        m = normalize_mechanic(str(item))
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


def mechanic_overlap(a: List[str], b: List[str]) -> List[str]:
    sa, sb = set(normalize_mechanics(a)), set(normalize_mechanics(b))
    return sorted(sa & sb)


def suggest_mechanics(partial: str, limit: int = 8) -> List[str]:
    needle = normalize_mechanic(partial)
    if not needle:
        return sorted(CANONICAL_MECHANICS)[:limit]
    hits = [m for m in CANONICAL_MECHANICS if needle in m]
    return hits[:limit]


def is_cooperative(mechanics: List[str]) -> bool:
    return "cooperative" in normalize_mechanics(mechanics)


def mechanic_family(mechanic: str) -> str:
    m = normalize_mechanic(mechanic)
    families = {
        "worker placement": "placement",
        "area control": "control",
        "tile placement": "placement",
        "pattern building": "abstract",
        "engine building": "engine",
    }
    return families.get(m, "other")


def rank_mechanics_by_plays(games: list, plays: list) -> List[tuple[str, int]]:
    from collections import Counter
    gmap = {g.id: g for g in games}
    c: Counter = Counter()
    for p in plays:
        g = gmap.get(p.game_id)
        if not g:
            continue
        for m in g.mechanics:
            c[m] += 1
    return c.most_common()


def filter_cooperative(games: list) -> list:
    return [g for g in games if is_cooperative(g.mechanics)]


def mechanic_graph(games: list) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for g in games:
        mechs = normalize_mechanics(g.mechanics)
        for i, a in enumerate(mechs):
            graph.setdefault(a, set())
            for b in mechs[i + 1 :]:
                graph.setdefault(b, set())
                graph[a].add(b)
                graph[b].add(a)
    return graph


def related_mechanics(games: list, mechanic: str, limit: int = 5) -> list[str]:
    graph = mechanic_graph(games)
    m = normalize_mechanic(mechanic)
    neighbors = graph.get(m, set())
    return sorted(neighbors)[:limit]

# TODO: community mechanic ontology file support
