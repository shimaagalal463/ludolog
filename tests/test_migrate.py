"""Tests for ludolog.migrate."""
import copy

import pytest

from ludolog.errors import MigrationError
from ludolog.migrate import (
    CURRENT_SCHEMA,
    describe_migration,
    ensure_migrated,
    migrate_v0_to_v1,
    migrate_v1_to_v2,
    migrate_v2_to_v3,
    migration_plan,
    preview_migrations,
)


def test_migrate_v0_to_v1_adds_core_lists(v0_fixture_data):
    result = migrate_v0_to_v1(v0_fixture_data)
    assert result["schema_version"] == 1
    assert result["games"] == v0_fixture_data["games"]
    assert result["plays"] == []
    assert result["players"] == []
    assert result["tags"] == []


def test_migrate_v1_to_v2_adds_shelves_and_play_defaults(v1_fixture_data):
    v1_fixture_data["plays"] = [{"id": 1, "game_id": 1, "played_at": "2025-01-01"}]
    result = migrate_v1_to_v2(v1_fixture_data)
    assert result["schema_version"] == 2
    assert result["shelves"] == []
    assert result["venues"] == []
    assert result["notes"] == []
    assert result["audit_log"] == []
    play = result["plays"][0]
    assert play["player_ids"] == []
    assert play["winner_ids"] == []
    assert play["scores"] == {}


def test_migrate_v2_to_v3_adds_seasons_and_game_defaults():
    data = {"schema_version": 2, "games": [{"id": 1, "title": "Test"}]}
    result = migrate_v2_to_v3(data)
    assert result["schema_version"] == 3
    assert result["seasons"] == []
    assert result["goals"] == []
    assert result["recurring_nights"] == []
    game = result["games"][0]
    assert game["mechanics"] == []
    assert game["owned"] is True
    assert game["wishlist"] is False


def test_ensure_migrated_v0_to_current(v0_fixture_data):
    migrated = ensure_migrated(v0_fixture_data)
    assert migrated["schema_version"] == CURRENT_SCHEMA
    assert "seasons" in migrated
    assert "recurring_nights" in migrated


def test_ensure_migrated_already_current(loaded_library):
    data = loaded_library.to_dict()
    migrated = ensure_migrated(data)
    assert migrated["schema_version"] == CURRENT_SCHEMA


def test_ensure_migrated_rejects_newer_schema():
    data = {"schema_version": CURRENT_SCHEMA + 1}
    with pytest.raises(MigrationError, match="newer than"):
        ensure_migrated(data)


def test_migration_plan_from_v0():
    assert migration_plan({"schema_version": 0}) == [0, 1, 2]


def test_migration_plan_when_current():
    assert migration_plan({"schema_version": CURRENT_SCHEMA}) == []


def test_migration_plan_from_v2():
    assert migration_plan({"schema_version": 2}) == [2]


def test_describe_migration_known_steps():
    assert describe_migration(0) == "bootstrap games/plays/players"
    assert describe_migration(1) == "add shelves, venues, notes"
    assert describe_migration(2) == "add seasons, goals, recurring nights"


def test_describe_migration_unknown():
    assert describe_migration(99) == "unknown"


def test_preview_migrations_lists_steps(v0_fixture_data):
    labels = preview_migrations(v0_fixture_data)
    assert labels == [
        "bootstrap games/plays/players",
        "add shelves, venues, notes",
        "add seasons, goals, recurring nights",
    ]


def test_migrate_v0_does_not_mutate_input(v0_fixture_data):
    original = copy.deepcopy(v0_fixture_data)
    migrate_v0_to_v1(v0_fixture_data)
    assert v0_fixture_data == original


def test_ensure_migrated_v1_fixture(v1_fixture_data):
    migrated = ensure_migrated(v1_fixture_data)
    assert migrated["schema_version"] == CURRENT_SCHEMA
    assert migrated["players"][0]["name"] == "Alex"


def test_ensure_migrated_preserves_games_through_chain(v0_fixture_data):
    migrated = ensure_migrated(v0_fixture_data)
    assert migrated["games"][0]["title"] == "Legacy Game"


def test_migrate_v1_to_v2_does_not_mutate_input(v1_fixture_data):
    original = copy.deepcopy(v1_fixture_data)
    migrate_v1_to_v2(v1_fixture_data)
    assert v1_fixture_data == original


def test_migrate_v2_to_v3_does_not_mutate_input():
    data = {"schema_version": 2, "games": []}
    original = copy.deepcopy(data)
    migrate_v2_to_v3(data)
    assert data == original


def test_ensure_migrated_idempotent(v0_fixture_data):
    once = ensure_migrated(v0_fixture_data)
    twice = ensure_migrated(once)
    assert twice["schema_version"] == CURRENT_SCHEMA
