"""Tests for ludolog.note."""
from ludolog.note import Note, latest_notes, notes_for_game, pinned_notes, search_notes


def test_note_to_dict_roundtrip(sample_note):
    restored = Note.from_dict(sample_note.to_dict())
    assert restored.body == "Great session!"
    assert restored.game_id == 1
    assert restored.created_at == "2025-06-01T21:00:00"


def test_notes_for_game_filters():
    n1 = Note(id=1, game_id=1, body="a")
    n2 = Note(id=2, game_id=2, body="b")
    n3 = Note(id=3, game_id=1, body="c")
    result = notes_for_game([n1, n2, n3], 1)
    assert result == [n1, n3]


def test_pinned_notes():
    pinned = Note(id=1, pinned=True, body="important")
    normal = Note(id=2, pinned=False, body="other")
    result = pinned_notes([normal, pinned])
    assert result == [pinned]


def test_search_notes_case_insensitive():
    notes = [
        Note(body="Catan was fun"),
        Note(body="Pandemic night"),
    ]
    hits = search_notes(notes, "CATAN")
    assert len(hits) == 1
    assert hits[0].body == "Catan was fun"


def test_latest_notes_sorted_descending():
    notes = [
        Note(created_at="2025-06-01T10:00:00", body="old"),
        Note(created_at="2025-06-03T10:00:00", body="new"),
        Note(created_at="2025-06-02T10:00:00", body="mid"),
    ]
    result = latest_notes(notes, limit=2)
    assert [n.body for n in result] == ["new", "mid"]


def test_latest_notes_respects_limit():
    notes = [Note(created_at=f"2025-06-0{i}T10:00:00") for i in range(1, 6)]
    assert len(latest_notes(notes, limit=3)) == 3


def test_search_notes_no_match():
    notes = [Note(body="hello world")]
    assert search_notes(notes, "zzzz") == []


def test_notes_for_game_empty():
    assert notes_for_game([Note(game_id=2)], 1) == []


def test_pinned_notes_empty():
    assert pinned_notes([Note(pinned=False)]) == []


def test_from_dict_defaults():
    note = Note.from_dict({"id": 7})
    assert note.body == ""
    assert note.pinned is False


def test_search_notes_partial_match():
    notes = [Note(body="engine building feels smooth")]
    assert search_notes(notes, "engine") == notes


def test_latest_notes_single_item():
    note = Note(created_at="2025-01-01", body="only")
    assert latest_notes([note]) == [note]
