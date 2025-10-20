"""Tests for ludolog.mechanics."""
from ludolog.game import Game
from ludolog.mechanics import (
    CANONICAL_MECHANICS,
    filter_cooperative,
    is_cooperative,
    mechanic_family,
    mechanic_graph,
    mechanic_overlap,
    normalize_mechanic,
    normalize_mechanics,
    rank_mechanics_by_plays,
    related_mechanics,
    suggest_mechanics,
)
from ludolog.play import Play


def test_normalize_mechanic_lowercase():
    assert normalize_mechanic("Worker Placement") == "worker placement"


def test_normalize_mechanic_underscores():
    assert normalize_mechanic("deck_building") == "deck building"


def test_normalize_mechanics_dedupes():
    result = normalize_mechanics(["Co-op", "cooperative", "Cooperative"])
    assert result == ["co op", "cooperative"]


def test_mechanic_overlap():
    overlap = mechanic_overlap(
        ["worker placement", "engine building"],
        ["engine building", "drafting"],
    )
    assert overlap == ["engine building"]


def test_suggest_mechanics_empty_returns_canonical():
    hits = suggest_mechanics("", limit=5)
    assert len(hits) == 5
    assert all(h in CANONICAL_MECHANICS for h in hits)


def test_suggest_mechanics_partial():
    hits = suggest_mechanics("deck")
    assert "deck building" in hits


def test_is_cooperative_true():
    assert is_cooperative(["cooperative"]) is True


def test_is_cooperative_false():
    assert is_cooperative(["auction"]) is False


def test_mechanic_family_known():
    assert mechanic_family("worker placement") == "placement"


def test_mechanic_family_unknown():
    assert mechanic_family("bluffing") == "other"


def test_rank_mechanics_by_plays():
    g = Game(id=1, mechanics=["auction", "bluffing"])
    plays = [Play(game_id=1), Play(game_id=1)]
    ranked = rank_mechanics_by_plays([g], plays)
    assert ranked[0][1] == 2


def test_filter_cooperative():
    coop = Game(mechanics=["cooperative"])
    comp = Game(mechanics=["auction"])
    result = filter_cooperative([coop, comp])
    assert len(result) == 1
    assert result[0].mechanics == ["cooperative"]


def test_mechanic_graph_links_neighbors():
    g = Game(mechanics=["auction", "bluffing"])
    graph = mechanic_graph([g])
    assert "bluffing" in graph["auction"]


def test_related_mechanics():
    g1 = Game(mechanics=["auction", "bluffing"])
    g2 = Game(mechanics=["auction", "negotiation"])
    related = related_mechanics([g1, g2], "auction")
    assert "bluffing" in related or "negotiation" in related


def test_normalize_mechanic_strips_whitespace():
    assert normalize_mechanic("  tile placement  ") == "tile placement"


def test_normalize_mechanics_skips_empty():
    assert normalize_mechanics(["", "  ", "drafting"]) == ["drafting"]


def test_suggest_mechanics_limit():
    hits = suggest_mechanics("", limit=3)
    assert len(hits) == 3


def test_canonical_mechanics_contains_cooperative():
    assert "cooperative" in CANONICAL_MECHANICS
