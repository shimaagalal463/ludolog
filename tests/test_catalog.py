"""Tests for ludolog.catalog."""
from __future__ import annotations

from ludolog.catalog import (
    apply_bulk_tags,
    bgg_ids_in_catalog,
    catalog_stats,
    dedupe_by_title,
    duplicate_groups,
    export_wishlist_titles,
    find_or_create_by_title,
    link_bgg,
    missing_bgg_ids,
    move_game_to_shelf,
    owned_games,
    prune_orphan_wishlist,
    sort_by_rating,
    split_by_owned,
    wishlist_games,
)
from ludolog.game import Game
from ludolog.play import Play


def test_duplicate_groups_finds_same_title(populated_library):
    dup = Game(title="catan", owned=False)
    populated_library.games.append(dup)
    groups = duplicate_groups(populated_library)
    assert len(groups) == 1
    assert len(groups[0]) == 2


def test_duplicate_groups_ignores_unique(populated_library):
    groups = duplicate_groups(populated_library)
    assert groups == []


def test_dedupe_by_title_merges_and_rewires_plays(tmp_journal, sample_game):
    dup = Game(title="Catan", bgg_id=999, designer="Other")
    tmp_journal.add_game(sample_game)
    tmp_journal.add_game(dup)
    play = Play(game_id=dup.id, played_at="2025-06-01", player_ids=[1])
    tmp_journal.add_play(play)
    merged = dedupe_by_title(tmp_journal)
    assert merged == 1
    assert len(tmp_journal.games) == 1
    assert tmp_journal.plays[0].game_id == sample_game.id
    assert tmp_journal.games[0].bgg_id == 13


def test_wishlist_games_excludes_owned(populated_library):
    wish = wishlist_games(populated_library)
    assert len(wish) == 1
    assert wish[0].title == "Ark Nova"


def test_owned_games_filters(populated_library):
    owned = owned_games(populated_library)
    assert len(owned) == 2
    assert all(g.owned for g in owned)


def test_catalog_stats_counts(populated_library):
    total, owned, wish = catalog_stats(populated_library)
    assert total == 3
    assert owned == 2
    assert wish == 1


def test_link_bgg_sets_id(populated_library):
    link_bgg(populated_library, game_id=2, bgg_id=12345)
    assert populated_library.get_game(2).bgg_id == 12345


def test_link_bgg_merges_existing_bgg_record(tmp_journal):
    a = Game(title="Game A", bgg_id=100)
    b = Game(title="Game B")
    tmp_journal.add_game(a)
    tmp_journal.add_game(b)
    play = Play(game_id=a.id, played_at="2025-06-01", player_ids=[1])
    tmp_journal.add_play(play)
    link_bgg(tmp_journal, game_id=b.id, bgg_id=100)
    assert len(tmp_journal.games) == 1
    assert tmp_journal.plays[0].game_id == b.id


def test_find_or_create_by_title_returns_existing(populated_library):
    g = find_or_create_by_title(populated_library, "Catan")
    assert g.id == 1
    assert len(populated_library.games) == 3


def test_find_or_create_by_title_creates_new(tmp_journal):
    g = find_or_create_by_title(tmp_journal, "Splendor")
    assert g.title == "Splendor"
    assert g.id == 1
    assert len(tmp_journal.games) == 1


def test_export_wishlist_titles_sorted(populated_library):
    titles = export_wishlist_titles(populated_library)
    assert titles == ["Ark Nova"]


def test_move_game_to_shelf(populated_library):
    move_game_to_shelf(populated_library, game_id=2, shelf_id=1)
    assert populated_library.get_game(2).shelf_id == 1


def test_split_by_owned(populated_library):
    owned, other = split_by_owned(populated_library)
    assert len(owned) == 2
    assert len(other) == 1
    assert other[0].wishlist is True


def test_bgg_ids_in_catalog(populated_library):
    ids = bgg_ids_in_catalog(populated_library)
    assert 13 in ids
    assert 30549 in ids


def test_missing_bgg_ids_owned_without_bgg(tmp_journal):
    g = Game(title="Homemade", owned=True, bgg_id=None)
    tmp_journal.add_game(g)
    missing = missing_bgg_ids(tmp_journal)
    assert len(missing) == 1
    assert missing[0].title == "Homemade"


def test_sort_by_rating_descending(populated_library):
    rated = sort_by_rating(populated_library, descending=True)
    assert rated[0].title == "Ark Nova"
    assert rated[-1].title == "Catan"


def test_apply_bulk_tags(tmp_journal, sample_game, sample_game2):
    tmp_journal.add_game(sample_game)
    tmp_journal.add_game(sample_game2)
    n = apply_bulk_tags(tmp_journal, [1, 2], "party")
    assert n == 2
    assert "party" in tmp_journal.get_game(1).tags
    assert "party" in tmp_journal.get_game(2).tags


def test_apply_bulk_tags_skips_existing(tmp_journal, sample_game):
    sample_game.tags = ["party"]
    tmp_journal.add_game(sample_game)
    n = apply_bulk_tags(tmp_journal, [1], "party")
    assert n == 0


def test_prune_orphan_wishlist(tmp_journal, sample_game):
    wish_dup = Game(title="Catan", wishlist=True, owned=False)
    tmp_journal.add_game(sample_game)
    tmp_journal.add_game(wish_dup)
    removed = prune_orphan_wishlist(tmp_journal)
    assert removed == 1
    assert len(tmp_journal.games) == 1
