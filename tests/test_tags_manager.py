"""Tests for ludolog.tags_manager."""
from __future__ import annotations

from ludolog.game import Game
from ludolog.tags_manager import (
    add_global_tag,
    all_tags,
    games_with_tag,
    normalize_tag,
    remove_global_tag,
    rename_tag,
    sync_global_tags_from_games,
    tag_cloud,
    untagged_games,
)


def test_normalize_tag():
    assert normalize_tag("  Co Op  ") == "co-op"
    assert normalize_tag("Family") == "family"


def test_add_global_tag_new(tmp_journal):
    assert add_global_tag(tmp_journal, "Strategy") is True
    assert "strategy" in tmp_journal.tags


def test_add_global_tag_duplicate(tmp_journal):
    add_global_tag(tmp_journal, "strategy")
    assert add_global_tag(tmp_journal, "Strategy") is False


def test_add_global_tag_empty(tmp_journal):
    assert add_global_tag(tmp_journal, "   ") is False


def test_remove_global_tag(tmp_journal):
    add_global_tag(tmp_journal, "party")
    assert remove_global_tag(tmp_journal, "Party") is True
    assert "party" not in tmp_journal.tags


def test_remove_global_tag_missing(tmp_journal):
    assert remove_global_tag(tmp_journal, "nope") is False


def test_all_tags_merges_global_and_game(populated_library):
    tags = all_tags(populated_library)
    assert "family" in tags
    assert "classic" in tags
    assert tags == sorted(tags)


def test_rename_tag_updates_games(tmp_journal, sample_game):
    sample_game.tags = ["old-tag"]
    tmp_journal.add_game(sample_game)
    tmp_journal.tags = ["old-tag"]
    changed = rename_tag(tmp_journal, "old-tag", "new-tag")
    assert changed == 1
    assert "new-tag" in tmp_journal.get_game(1).tags
    assert "new-tag" in tmp_journal.tags


def test_games_with_tag(populated_library):
    ids = games_with_tag(populated_library, "Classic")
    assert 1 in ids


def test_tag_cloud_counts(populated_library):
    cloud = tag_cloud(populated_library)
    assert isinstance(cloud[0], tuple)
    tags = dict(cloud)
    assert tags.get("family", 0) >= 1


def test_untagged_games(populated_library):
    untagged = untagged_games(populated_library)
    assert any(g.title == "Pandemic" for g in untagged)
    assert all(not g.tags for g in untagged)


def test_sync_global_tags_from_games(tmp_journal, sample_game):
    sample_game.tags = ["engine-building", "heavy"]
    tmp_journal.add_game(sample_game)
    added = sync_global_tags_from_games(tmp_journal)
    assert added == 2
    assert "engine-building" in tmp_journal.tags


def test_sync_global_tags_skips_existing(populated_library):
    before = len(populated_library.tags)
    added = sync_global_tags_from_games(populated_library)
    assert added >= 0
    assert len(all_tags(populated_library)) >= before


def test_games_with_tag_no_matches(tmp_journal, sample_game):
    sample_game.tags = ["solo"]
    tmp_journal.add_game(sample_game)
    assert games_with_tag(tmp_journal, "party") == []


def test_rename_tag_zero_changes(tmp_journal):
    assert rename_tag(tmp_journal, "missing", "other") == 0


def test_untagged_after_adding_tag(tmp_journal):
    g = Game(title="Bare", tags=[])
    tmp_journal.add_game(g)
    assert len(untagged_games(tmp_journal)) == 1
    g.add_tag("tagged")
    assert len(untagged_games(tmp_journal)) == 0
