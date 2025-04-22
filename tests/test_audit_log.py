"""Tests for ludolog.audit_log."""
import pytest

from ludolog.audit_log import (
    AuditEntry,
    audit_for_entity,
    filter_audit,
    log_action,
    recent_actions,
)
from ludolog.storage import Library


@pytest.fixture
def fresh_library(tmp_path):
    """Library without init_library save audit noise."""
    lib = Library(path=tmp_path / "fresh.json")
    lib.audit_log.clear()
    return lib


def test_audit_entry_roundtrip():
    entry = AuditEntry(at="2025-06-01T12:00:00", action="game.add", detail={"id": 1})
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.at == entry.at
    assert restored.action == entry.action
    assert restored.detail == {"id": 1}


def test_log_action_appends_entry(fresh_library):
    log_action(fresh_library, "library.init", {"path": "test.json"})
    assert len(fresh_library.audit_log) == 1
    assert fresh_library.audit_log[0].action == "library.init"
    assert fresh_library.audit_log[0].detail == {"path": "test.json"}


def test_log_action_default_empty_detail(fresh_library):
    log_action(fresh_library, "ping")
    assert fresh_library.audit_log[0].detail == {}


def test_recent_actions_returns_newest_first(tmp_journal):
    for i in range(3):
        log_action(tmp_journal, f"step.{i}", {"n": i})
    recent = recent_actions(tmp_journal, limit=2)
    assert [e.action for e in recent] == ["step.2", "step.1"]


def test_recent_actions_respects_limit(tmp_journal):
    for i in range(5):
        log_action(tmp_journal, f"evt.{i}")
    assert len(recent_actions(tmp_journal, limit=3)) == 3


def test_filter_audit_by_prefix(tmp_journal):
    log_action(tmp_journal, "game.add", {"id": 1})
    log_action(tmp_journal, "game.remove", {"id": 1})
    log_action(tmp_journal, "play.add", {"id": 2})
    game_events = filter_audit(tmp_journal, "game.")
    assert len(game_events) == 2
    assert all(e.action.startswith("game.") for e in game_events)


def test_audit_for_entity_matches_id_in_detail(tmp_journal):
    log_action(tmp_journal, "game.update", {"id": 42, "field": "title"})
    log_action(tmp_journal, "game.update", {"id": 99})
    hits = audit_for_entity(tmp_journal, "game", 42)
    assert len(hits) == 1
    assert hits[0].detail["id"] == 42


def test_audit_for_entity_matches_entity_key(fresh_library):
    log_action(fresh_library, "shelf.move", {"shelf": 3, "game": 7})
    hits = audit_for_entity(fresh_library, "shelf", 3)
    assert len(hits) == 1
    assert hits[0].detail["shelf"] == 3


def test_audit_for_entity_matches_value_in_detail(tmp_journal):
    log_action(tmp_journal, "import", {"source": "bgg", "matched": "13"})
    hits = audit_for_entity(tmp_journal, "bgg", 13)
    assert len(hits) == 1


def test_log_action_trims_to_500_entries(tmp_journal):
    for i in range(505):
        log_action(tmp_journal, "bulk", {"i": i})
    assert len(tmp_journal.audit_log) == 500
    assert tmp_journal.audit_log[0].detail["i"] == 5
    assert tmp_journal.audit_log[-1].detail["i"] == 504


def test_audit_entry_from_dict_defaults():
    entry = AuditEntry.from_dict({"action": "noop"})
    assert entry.at == ""
    assert entry.detail == {}


def test_recent_actions_empty_library(fresh_library):
    assert recent_actions(fresh_library) == []


def test_filter_audit_no_matches(tmp_journal):
    log_action(tmp_journal, "play.add")
    assert filter_audit(tmp_journal, "game.") == []


def test_log_action_timestamp_is_iso_format(tmp_journal):
    log_action(tmp_journal, "test")
    assert "T" in tmp_journal.audit_log[0].at


def test_audit_for_entity_no_matches(tmp_journal):
    log_action(tmp_journal, "other", {"id": 1})
    assert audit_for_entity(tmp_journal, "game", 99) == []
