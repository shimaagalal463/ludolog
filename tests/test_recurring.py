"""Tests for ludolog.recurring."""
from __future__ import annotations

from ludolog.game import Game
from ludolog.recurring import (
    WEEKDAYS,
    RecurringNight,
    active_nights,
    attach_player_to_night,
    deactivate_night,
    next_night_label,
    nights_on_weekday,
    suggest_games_for_night,
)


def test_recurring_night_to_dict_roundtrip(sample_recurring):
    data = sample_recurring.to_dict()
    restored = RecurringNight.from_dict(data)
    assert restored.name == "Friday Night"
    assert restored.weekday == "fri"
    assert restored.usual_player_ids == [1]


def test_from_dict_weekday_truncation():
    night = RecurringNight.from_dict({"weekday": "Friday"})
    assert night.weekday == "fri"


def test_from_dict_preferred_game_ids():
    night = RecurringNight.from_dict({"preferred_game_ids": [1, 2]})
    assert night.preferred_game_ids == [1, 2]


def test_from_dict_default_venue_id():
    night = RecurringNight.from_dict({"default_venue_id": 5})
    assert night.default_venue_id == 5


def test_weekday_label(sample_recurring):
    assert sample_recurring.weekday_label() == "Fri"


def test_weekdays_constant():
    assert len(WEEKDAYS) == 7
    assert "fri" in WEEKDAYS


def test_active_nights_filters_inactive():
    active = RecurringNight(name="Active", active=True)
    inactive = RecurringNight(name="Old", active=False)
    result = active_nights([active, inactive])
    assert result == [active]


def test_nights_on_weekday(populated_library):
    nights = populated_library.recurring_nights
    fri = nights_on_weekday(nights, "fri")
    assert len(fri) == 1
    assert fri[0].name == "Friday Night"


def test_nights_on_weekday_excludes_inactive():
    night = RecurringNight(weekday="sat", active=False)
    assert nights_on_weekday([night], "sat") == []


def test_next_night_label(sample_recurring):
    label = next_night_label(sample_recurring)
    assert "Fri" in label
    assert "19:00" in label
    assert "Friday Night" in label


def test_suggest_games_for_night(populated_library):
    night = RecurringNight(preferred_game_ids=[1, 2, 999])
    games = suggest_games_for_night(night, populated_library)
    assert len(games) == 2
    assert all(isinstance(g, Game) for g in games)


def test_attach_player_to_night_adds_id(sample_recurring):
    attach_player_to_night(sample_recurring, 2)
    assert 2 in sample_recurring.usual_player_ids


def test_attach_player_to_night_no_duplicate(sample_recurring):
    attach_player_to_night(sample_recurring, 1)
    assert sample_recurring.usual_player_ids.count(1) == 1


def test_deactivate_night(sample_recurring):
    assert sample_recurring.active is True
    deactivate_night(sample_recurring)
    assert sample_recurring.active is False


def test_from_dict_normalizes_weekday_for_matching():
    night = RecurringNight.from_dict({"weekday": "Saturday", "active": True})
    result = nights_on_weekday([night], "sat")
    assert result == [night]
