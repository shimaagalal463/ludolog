"""Tests for ludolog.venue."""
from ludolog.play import Play
from ludolog.storage import Library
from ludolog.venue import Venue, default_venue, find_venue, venue_play_counts


def test_venue_to_dict_roundtrip(sample_venue):
    restored = Venue.from_dict(sample_venue.to_dict())
    assert restored.name == "Game Cafe"
    assert restored.address == "123 Main St"
    assert restored.default_for_nights is True


def test_default_venue_prefers_flagged():
    default = Venue(id=1, name="Home", default_for_nights=True)
    other = Venue(id=2, name="Cafe", default_for_nights=False)
    assert default_venue([other, default]) is default


def test_default_venue_falls_back_to_first():
    a = Venue(id=1, name="A")
    b = Venue(id=2, name="B")
    assert default_venue([a, b]) is a


def test_default_venue_empty_list():
    assert default_venue([]) is None


def test_find_venue(sample_venue):
    venues = [sample_venue, Venue(id=2, name="Other")]
    assert find_venue(venues, 1) is sample_venue
    assert find_venue(venues, 99) is None


def test_venue_play_counts_from_populated_library(populated_library, sample_venue):
    counts = venue_play_counts(populated_library)
    assert counts == [("Game Cafe", 1)]


def test_venue_play_counts_ignores_unknown_venue_id():
    lib = Library(path=None)
    lib.venues = [Venue(id=1, name="Known")]
    lib.plays = [
        Play(id=1, game_id=1, played_at="2025-06-01", venue_id=1),
        Play(id=2, game_id=1, played_at="2025-06-02", venue_id=99),
        Play(id=3, game_id=1, played_at="2025-06-03", venue_id=None),
    ]
    assert venue_play_counts(lib) == [("Known", 1)]


def test_venue_play_counts_orders_by_frequency():
    lib = Library(path=None)
    lib.venues = [
        Venue(id=1, name="Rare"),
        Venue(id=2, name="Popular"),
    ]
    lib.plays = [
        Play(id=1, game_id=1, played_at="2025-06-01", venue_id=2),
        Play(id=2, game_id=1, played_at="2025-06-02", venue_id=2),
        Play(id=3, game_id=1, played_at="2025-06-03", venue_id=1),
    ]
    counts = venue_play_counts(lib)
    assert counts[0] == ("Popular", 2)
    assert counts[1] == ("Rare", 1)


def test_from_dict_defaults():
    venue = Venue.from_dict({"id": 4})
    assert venue.name == ""
    assert venue.default_for_nights is False


def test_find_venue_empty_list():
    assert find_venue([], 1) is None


def test_venue_play_counts_empty_library():
    lib = Library(path=None)
    assert venue_play_counts(lib) == []


def test_default_venue_single_non_default():
    only = Venue(id=1, name="Solo", default_for_nights=False)
    assert default_venue([only]) is only
