"""Tests for ludolog.timeline."""
from __future__ import annotations

from ludolog.note import Note
from ludolog.play import Play
from ludolog.timeline import (
    TimelineEvent,
    build_timeline,
    filter_timeline,
    group_timeline_by_day,
    merge_timelines,
    timeline_as_text,
    timeline_for_game,
)


def test_build_timeline_includes_plays(populated_library):
    events = build_timeline(populated_library)
    play_events = [e for e in events if e.kind == "play"]
    assert len(play_events) >= 1
    assert "Catan" in play_events[0].summary


def test_build_timeline_includes_notes(populated_library):
    events = build_timeline(populated_library)
    note_events = [e for e in events if e.kind == "note"]
    assert len(note_events) == 1
    assert "Great session" in note_events[0].summary


def test_build_timeline_newest_first(populated_library):
    populated_library.add_play(
        Play(game_id=1, played_at="2024-01-01T10:00:00", player_ids=[1])
    )
    events = build_timeline(populated_library, limit=10)
    assert events[0].when >= events[-1].when


def test_build_timeline_respects_limit(populated_library):
    for i in range(5):
        populated_library.add_note(
            Note(body=f"note {i}", created_at=f"2025-06-{i+1:02d}T12:00:00")
        )
    events = build_timeline(populated_library, limit=3)
    assert len(events) == 3


def test_build_timeline_missing_game_fallback(tmp_journal):
    tmp_journal.plays.append(
        Play(id=1, game_id=42, played_at="2025-06-01T10:00:00", player_ids=[1, 2])
    )
    events = build_timeline(tmp_journal)
    assert "game #42" in events[0].summary
    assert "2 players" in events[0].summary


def test_timeline_for_game(populated_library, sample_game):
    populated_library.add_play(
        Play(game_id=2, played_at="2025-06-10T10:00:00", player_ids=[1, 2])
    )
    events = timeline_for_game(populated_library.plays, sample_game)
    assert all("Catan" in e.summary for e in events)
    assert len(events) == 1


def test_timeline_for_game_sorted_newest(populated_library, sample_game):
    older = Play(game_id=1, played_at="2025-05-01T10:00:00", player_ids=[1])
    newer = Play(game_id=1, played_at="2025-06-20T10:00:00", player_ids=[1, 2])
    populated_library.add_play(older)
    populated_library.add_play(newer)
    events = timeline_for_game(populated_library.plays, sample_game)
    assert events[0].when == newer.played_at


def test_timeline_as_text(populated_library):
    text = timeline_as_text(populated_library, limit=5)
    lines = text.split("\n")
    assert len(lines) >= 2
    assert lines[0].startswith("2025")
    assert "[play]" in lines[0] or "[note]" in lines[0]


def test_filter_timeline_by_kind():
    events = [
        TimelineEvent(when="2025-06-01", kind="play", summary="a", ref_id=1),
        TimelineEvent(when="2025-06-02", kind="note", summary="b", ref_id=2),
    ]
    plays = filter_timeline(events, "play")
    assert len(plays) == 1
    assert plays[0].ref_id == 1


def test_filter_timeline_empty_result():
    events = [TimelineEvent(when="2025-06-01", kind="play", summary="a", ref_id=1)]
    assert filter_timeline(events, "note") == []


def test_merge_timelines_sorts():
    a = [TimelineEvent(when="2025-06-01", kind="play", summary="old", ref_id=1)]
    b = [TimelineEvent(when="2025-06-10", kind="note", summary="new", ref_id=2)]
    merged = merge_timelines(a, b)
    assert merged[0].when == "2025-06-10"
    assert len(merged) == 2


def test_merge_timelines_empty():
    assert merge_timelines([], []) == []


def test_group_timeline_by_day(populated_library):
    buckets = group_timeline_by_day(populated_library)
    assert "2025-06-01" in buckets
    assert any(e.kind == "play" for e in buckets["2025-06-01"])


def test_group_timeline_unknown_day(tmp_journal):
    tmp_journal.notes.append(Note(id=1, body="no date", created_at=""))
    buckets = group_timeline_by_day(tmp_journal)
    assert "unknown" in buckets


def test_timeline_event_fields():
    ev = TimelineEvent(when="2025-06-01T19:00:00", kind="play", summary="test", ref_id=7)
    assert ev.when == "2025-06-01T19:00:00"
    assert ev.kind == "play"
    assert ev.ref_id == 7
