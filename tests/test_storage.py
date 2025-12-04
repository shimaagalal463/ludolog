"""Tests for ludolog.storage."""
from __future__ import annotations

import json

import pytest

from ludolog.errors import NotFoundError, StorageError, ValidationError
from ludolog.game import Game
from ludolog.play import Play
from ludolog.player import Player
from ludolog.storage import (
    Library,
    add_recurring_night,
    archive_player,
    assign_season_to_plays,
    attach_game_to_shelf,
    compact_library,
    compute_library_health,
    count_owned_games,
    count_wishlist,
    describe_library,
    export_player_directory,
    games_on_shelf,
    games_without_shelf,
    import_player_directory,
    init_library,
    library_summary,
    merge_player_records,
    plays_at_venue,
    reactivate_player,
    recent_plays,
    remove_game,
    remove_play,
    set_game_rating,
    suggest_next_game,
    toggle_wishlist,
    validate_references,
)


def test_init_library_creates_file(tmp_path):
    path = tmp_path / "new.json"
    lib = init_library(path)
    assert path.exists()
    assert lib.games == []
    assert lib.schema_version >= 1


def test_save_and_load_roundtrip(populated_library, tmp_path):
    path = populated_library.path
    populated_library.save()
    loaded = Library.load(path)
    assert len(loaded.games) == len(populated_library.games)
    assert loaded.get_game(1).title == "Catan"
    assert len(loaded.plays) == 1


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(StorageError, match="missing journal"):
        Library.load(tmp_path / "nope.json")


def test_load_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(StorageError, match="invalid JSON"):
        Library.load(bad)


def test_add_game_assigns_incremental_id(tmp_journal, sample_game):
    g = tmp_journal.add_game(sample_game)
    assert g.id == 1
    g2 = tmp_journal.add_game(Game(title="Azul"))
    assert g2.id == 2


def test_add_play_and_get_play(tmp_journal, sample_game, sample_play):
    tmp_journal.add_game(sample_game)
    p = tmp_journal.add_play(sample_play)
    assert p.id == 1
    assert tmp_journal.get_play(1).game_id == sample_game.id


def test_get_game_not_found_raises(tmp_journal):
    with pytest.raises(NotFoundError, match="game 99"):
        tmp_journal.get_game(99)


def test_add_player_assigns_id(tmp_journal, sample_player):
    p = tmp_journal.add_player(sample_player)
    assert p.id == 1
    assert tmp_journal.get_player(1).name == "Alice"


def test_remove_game_cascades_plays_and_collection(populated_library):
    populated_library.collections[0].game_ids = [1, 2]
    remove_game(populated_library, 1)
    assert all(g.id != 1 for g in populated_library.games)
    assert all(p.game_id != 1 for p in populated_library.plays)
    assert 1 not in populated_library.collections[0].game_ids


def test_remove_play(tmp_journal, sample_game, sample_play):
    tmp_journal.add_game(sample_game)
    tmp_journal.add_play(sample_play)
    remove_play(tmp_journal, 1)
    assert tmp_journal.plays == []


def test_merge_player_records_rewrites_plays(populated_library):
    dup = Player(name="Alice Duplicate")
    populated_library.add_player(dup)
    play = Play(
        game_id=1,
        played_at="2025-06-03T20:00:00",
        player_ids=[dup.id, 2],
        winner_ids=[dup.id],
        scores={str(dup.id): 12.0},
    )
    populated_library.add_play(play)
    keeper = merge_player_records(populated_library, keep_id=1, drop_id=dup.id)
    assert keeper.id == 1
    assert dup.id not in [p.id for p in populated_library.players]
    merged_play = populated_library.get_play(play.id)
    assert 1 in merged_play.player_ids
    assert merged_play.scores.get("1") == 12.0


def test_validate_references_clean(populated_library):
    assert validate_references(populated_library) == []


def test_validate_references_detects_broken_game(tmp_journal):
    tmp_journal.plays.append(Play(id=1, game_id=999, played_at="2025-01-01"))
    problems = validate_references(tmp_journal)
    assert any("missing game 999" in msg for msg in problems)


def test_attach_game_to_shelf(populated_library):
    game = attach_game_to_shelf(populated_library, game_id=2, shelf_id=1)
    assert game.shelf_id == 1
    on_shelf = games_on_shelf(populated_library, 1)
    assert any(g.id == 2 for g in on_shelf)


def test_plays_at_venue(populated_library):
    venue_plays = plays_at_venue(populated_library, 1)
    assert len(venue_plays) == 1
    assert venue_plays[0].venue_id == 1


def test_library_summary_counts(populated_library):
    summary = library_summary(populated_library)
    assert summary["games"] == 3
    assert summary["plays"] == 1
    assert summary["players"] == 2


def test_count_owned_and_wishlist(populated_library):
    assert count_owned_games(populated_library) == 2
    assert count_wishlist(populated_library) == 1


def test_import_player_directory_skips_duplicates(populated_library):
    rows = [{"name": "Alice", "handle": "alice"}, {"name": "Charlie", "handle": "charlie"}]
    added = import_player_directory(populated_library, rows)
    assert added == 1
    assert any(p.name == "Charlie" for p in populated_library.players)


def test_export_player_directory(populated_library):
    directory = export_player_directory(populated_library)
    assert directory[0]["name"] == "Alice"
    assert "active" in directory[0]


def test_archive_and_reactivate_player(populated_library):
    archive_player(populated_library, 1)
    assert populated_library.get_player(1).active is False
    reactivate_player(populated_library, 1)
    assert populated_library.get_player(1).active is True


def test_set_game_rating_and_toggle_wishlist(populated_library):
    set_game_rating(populated_library, 1, 9.25)
    assert populated_library.get_game(1).rating == 9.25
    toggle_wishlist(populated_library, 2, wishlist=True)
    g = populated_library.get_game(2)
    assert g.wishlist is True
    assert g.owned is False


def test_set_game_rating_invalid_raises(populated_library):
    with pytest.raises(ValidationError):
        set_game_rating(populated_library, 1, 11.0)


def test_recent_plays_newest_first(populated_library):
    older = Play(game_id=1, played_at="2025-05-01T10:00:00", player_ids=[1])
    newer = Play(game_id=2, played_at="2025-06-15T10:00:00", player_ids=[1])
    populated_library.add_play(older)
    populated_library.add_play(newer)
    recent = recent_plays(populated_library, limit=2)
    assert recent[0].played_at == newer.played_at


def test_games_without_shelf(populated_library):
    unassigned = games_without_shelf(populated_library)
    assert any(g.id == 2 for g in unassigned)
    assert all(g.owned for g in unassigned)


def test_compact_library_merges_duplicate_titles(tmp_journal, sample_game):
    dup = Game(title="Catan", owned=False, wishlist=True)
    tmp_journal.add_game(sample_game)
    tmp_journal.add_game(dup)
    result = compact_library(tmp_journal)
    assert result["merged"] == 1
    assert result["pruned"] == 0
    assert len(tmp_journal.games) == 1


def test_suggest_next_game_prefers_unplayed(populated_library):
    suggestions = suggest_next_game(populated_library, players=4, minutes=75)
    titles = [g.title for g in suggestions]
    assert "Pandemic" in titles or "Catan" in titles
    assert all(g.fits_players(4) for g in suggestions)


def test_compute_library_health(populated_library):
    health = compute_library_health(populated_library)
    assert health["broken_refs"] == 0
    assert health["unplayed_owned"] >= 1
    assert health["open_goals"] >= 1


def test_describe_library_format(populated_library):
    text = describe_library(populated_library)
    assert text.startswith("Library(")
    assert "games=3" in text


def test_add_recurring_night(populated_library, sample_recurring):
    night = add_recurring_night(populated_library, sample_recurring)
    assert night.id == 2
    assert len(populated_library.recurring_nights) == 2


def test_to_dict_from_dict_roundtrip(tmp_journal, sample_game, sample_player):
    tmp_journal.add_game(sample_game)
    tmp_journal.add_player(sample_player)
    data = tmp_journal.to_dict()
    restored = Library.from_dict(tmp_journal.path, data)
    assert restored.games[0].title == "Catan"
    assert restored.players[0].name == "Alice"


def test_loaded_library_from_fixture(loaded_library):
    assert loaded_library.get_game(1).title == "Wingspan"
    assert len(loaded_library.plays) == 1


def test_assign_season_to_plays(populated_library):
    populated_library.plays[0].season_id = None
    assigned = assign_season_to_plays(populated_library)
    assert assigned == 1
    assert populated_library.plays[0].season_id == 1


def test_init_library_json_structure(tmp_path):
    path = tmp_path / "fresh.json"
    init_library(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert "games" in raw
    assert raw["games"] == []
