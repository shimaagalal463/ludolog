"""Tests for ludolog.player."""
from ludolog.player import (
    Player,
    active_players,
    find_player_by_name,
    inactive_players,
    merge_handles,
    player_map,
    resolve_player_names,
    sort_by_name,
)


def test_display_name_prefers_handle():
    p = Player(name="Alice Smith", handle="alice")
    assert p.display_name() == "alice"


def test_display_name_falls_back_to_name():
    p = Player(name="Alice Smith")
    assert p.display_name() == "Alice Smith"


def test_matches_query_name():
    p = Player(name="Charlie Brown")
    assert p.matches_query("charlie") is True


def test_matches_query_handle():
    p = Player(name="X", handle="gamer42")
    assert p.matches_query("gamer") is True


def test_matches_query_no_match():
    p = Player(name="Alice")
    assert p.matches_query("bob") is False


def test_to_dict_roundtrip():
    p = Player(id=1, name="Alice", handle="a", email="a@x.com", favorite_mechanics=["drafting"])
    restored = Player.from_dict(p.to_dict())
    assert restored.name == "Alice"
    assert restored.favorite_mechanics == ["drafting"]


def test_find_player_by_name_exact():
    players = [Player(id=1, name="Alice"), Player(id=2, name="Bob")]
    assert find_player_by_name(players, "alice").id == 1


def test_find_player_by_handle():
    players = [Player(id=1, name="Alice", handle="ali")]
    assert find_player_by_name(players, "ali").id == 1


def test_find_player_by_name_missing():
    assert find_player_by_name([], "Nobody") is None


def test_resolve_player_names():
    players = [Player(id=1, name="Alice"), Player(id=2, name="Bob")]
    ids = resolve_player_names(players, ["Alice", "Unknown"])
    assert ids == [1]


def test_active_players():
    players = [Player(active=True), Player(active=False)]
    assert len(active_players(players)) == 1


def test_inactive_players():
    players = [Player(active=True), Player(active=False)]
    assert len(inactive_players(players)) == 1


def test_sort_by_name():
    players = [Player(name="Zara"), Player(name="Amy")]
    sorted_p = sort_by_name(players)
    assert sorted_p[0].name == "Amy"


def test_player_map():
    players = [Player(id=1, name="A"), Player(id=2, name="B")]
    m = player_map(players)
    assert m[2].name == "B"


def test_merge_handles():
    players = [Player(handle="a"), Player(handle="b"), Player(handle="")]
    assert merge_handles(players) == ["a", "b"]


def test_from_dict_defaults():
    p = Player.from_dict({})
    assert p.active is True
    assert p.name == ""


def test_matches_query_case_insensitive():
    p = Player(name="ALICE")
    assert p.matches_query("alice") is True
