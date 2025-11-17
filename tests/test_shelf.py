"""Tests for ludolog.shelf."""
from ludolog.game import Game
from ludolog.shelf import Shelf, find_shelf, full_shelves, shelf_usage, shelves_with_capacity


def test_shelf_to_dict_roundtrip(sample_shelf):
    restored = Shelf.from_dict(sample_shelf.to_dict())
    assert restored.name == "Living Room"
    assert restored.location == "Home"
    assert restored.capacity == 20


def test_room_label_with_location(sample_shelf):
    assert sample_shelf.room_label() == "Living Room (Home)"


def test_room_label_without_location():
    shelf = Shelf(name="Garage", location="")
    assert shelf.room_label() == "Garage"


def test_shelf_usage_with_capacity(sample_shelf):
    assert shelf_usage(10, sample_shelf) == 0.5


def test_shelf_usage_no_capacity():
    shelf = Shelf(capacity=None)
    assert shelf_usage(5, shelf) is None


def test_find_shelf(sample_shelf):
    shelves = [sample_shelf, Shelf(id=2, name="Other")]
    assert find_shelf(shelves, 1) is sample_shelf
    assert find_shelf(shelves, 99) is None


def test_shelves_with_capacity():
    with_cap = Shelf(id=1, capacity=10)
    without = Shelf(id=2, capacity=None)
    zero = Shelf(id=3, capacity=0)
    result = shelves_with_capacity([with_cap, without, zero])
    assert result == [with_cap]


def test_full_shelves_detects_at_capacity(populated_library, sample_shelf):
    for i in range(18):
        populated_library.games.append(
            Game(id=100 + i, title=f"Filler {i}", shelf_id=sample_shelf.id)
        )
    assert full_shelves(populated_library) == []
    populated_library.games.append(
        Game(id=200, title="At capacity", shelf_id=sample_shelf.id)
    )
    full = full_shelves(populated_library)
    assert len(full) == 1
    assert full[0].id == sample_shelf.id


def test_from_dict_defaults():
    shelf = Shelf.from_dict({"id": 3})
    assert shelf.name == ""
    assert shelf.notes == ""


def test_shelf_usage_zero_capacity_returns_none():
    shelf = Shelf(capacity=0)
    assert shelf_usage(3, shelf) is None


def test_find_shelf_empty_list():
    assert find_shelf([], 1) is None


def test_full_shelves_ignores_under_capacity(populated_library):
    assert full_shelves(populated_library) == []
