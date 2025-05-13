"""Tests for ludolog.collections."""
from ludolog.collections import (
    Collection,
    collection_size,
    collections_by_name,
    collections_for_game,
    merge_collections,
    pinned_collections,
)


def test_collection_to_dict_roundtrip(sample_collection):
    restored = Collection.from_dict(sample_collection.to_dict())
    assert restored.name == "Favorites"
    assert restored.game_ids == [1]
    assert restored.pinned is True


def test_add_game_returns_true_once(sample_collection):
    assert sample_collection.add_game(2) is True
    assert 2 in sample_collection.game_ids
    assert sample_collection.add_game(2) is False


def test_remove_game(sample_collection):
    assert sample_collection.remove_game(1) is True
    assert 1 not in sample_collection.game_ids
    assert sample_collection.remove_game(99) is False


def test_contains(sample_collection):
    assert sample_collection.contains(1) is True
    assert sample_collection.contains(2) is False


def test_collections_for_game():
    a = Collection(id=1, name="A", game_ids=[1, 2])
    b = Collection(id=2, name="B", game_ids=[3])
    c = Collection(id=3, name="C", game_ids=[2])
    hits = collections_for_game([a, b, c], 2)
    assert {x.name for x in hits} == {"A", "C"}


def test_pinned_collections():
    pinned = Collection(id=1, name="Pinned", pinned=True)
    normal = Collection(id=2, name="Normal", pinned=False)
    result = pinned_collections([normal, pinned])
    assert len(result) == 1
    assert result[0].name == "Pinned"


def test_collection_size(sample_collection):
    assert collection_size(sample_collection) == 1
    sample_collection.add_game(5)
    assert collection_size(sample_collection) == 2


def test_merge_collections_counts_new_only():
    target = Collection(id=1, name="Target", game_ids=[1, 2])
    source = Collection(id=2, name="Source", game_ids=[2, 3, 4])
    added = merge_collections(target, source)
    assert added == 2
    assert sorted(target.game_ids) == [1, 2, 3, 4]


def test_collections_by_name_case_insensitive():
    coll = Collection(id=1, name="Party Games")
    assert collections_by_name([coll], "  party games ") is coll
    assert collections_by_name([coll], "Travel") is None


def test_from_dict_coerces_game_ids():
    coll = Collection.from_dict({"id": 1, "game_ids": ["1", "2"]})
    assert coll.game_ids == [1, 2]


def test_merge_collections_no_new_games():
    target = Collection(game_ids=[1, 2])
    source = Collection(game_ids=[1, 2])
    assert merge_collections(target, source) == 0


def test_collections_for_game_empty():
    assert collections_for_game([Collection(game_ids=[1])], 99) == []


def test_pinned_collections_empty():
    assert pinned_collections([Collection(pinned=False)]) == []


def test_collection_from_dict_defaults():
    coll = Collection.from_dict({"id": 5})
    assert coll.name == ""
    assert coll.game_ids == []
    assert coll.pinned is False


def test_remove_game_preserves_order():
    coll = Collection(game_ids=[1, 2, 3])
    coll.remove_game(2)
    assert coll.game_ids == [1, 3]
