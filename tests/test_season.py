"""Tests for ludolog.season."""
from ludolog.play import Play
from ludolog.season import (
    Season,
    assign_play_seasons,
    current_season,
    list_season_names,
    overlapping_seasons,
    season_play_count,
)


def test_season_to_dict_roundtrip(sample_season):
    restored = Season.from_dict(sample_season.to_dict())
    assert restored.name == "Summer 2025"
    assert restored.start_date == "2025-06-01"
    assert restored.end_date == "2025-08-31"


def test_contains_date_inside_range(sample_season):
    assert sample_season.contains_date("2025-07-15") is True


def test_contains_date_before_start(sample_season):
    assert sample_season.contains_date("2025-05-31") is False


def test_contains_date_after_end(sample_season):
    assert sample_season.contains_date("2025-09-01") is False


def test_contains_date_open_bounds():
    season = Season(start_date="", end_date="")
    assert season.contains_date("2020-01-01") is True


def test_current_season_finds_match(sample_season):
    seasons = [Season(name="Winter", start_date="2025-01-01", end_date="2025-03-31"), sample_season]
    assert current_season(seasons, "2025-07-01") is sample_season


def test_current_season_none_when_no_match(sample_season):
    assert current_season([sample_season], "2024-12-01") is None


def test_assign_play_seasons_sets_matching_id(sample_season):
    play = Play(id=1, game_id=1, played_at="2025-07-10T18:00:00")
    assign_play_seasons([play], [sample_season])
    assert play.season_id == sample_season.id


def test_assign_play_seasons_skips_existing_season_id(sample_season):
    play = Play(id=1, game_id=1, played_at="2025-07-10", season_id=99)
    assign_play_seasons([play], [sample_season])
    assert play.season_id == 99


def test_season_play_count(sample_season):
    plays = [
        Play(id=1, game_id=1, played_at="2025-06-15"),
        Play(id=2, game_id=1, played_at="2025-09-01"),
        Play(id=3, game_id=1, played_at="2025-07-01T20:00:00"),
    ]
    assert season_play_count(sample_season, plays) == 2


def test_list_season_names():
    seasons = [Season(name="A"), Season(name="B")]
    assert list_season_names(seasons) == ["A", "B"]


def test_overlapping_seasons_detects_overlap():
    a = Season(name="A", start_date="2025-01-01", end_date="2025-06-30")
    b = Season(name="B", start_date="2025-06-01", end_date="2025-12-31")
    pairs = overlapping_seasons([a, b])
    assert pairs == [(a, b)]


def test_overlapping_seasons_no_overlap():
    a = Season(name="A", start_date="2025-01-01", end_date="2025-03-31")
    b = Season(name="B", start_date="2025-04-01", end_date="2025-06-30")
    assert overlapping_seasons([a, b]) == []


def test_assign_play_seasons_no_match_leaves_unset(sample_season):
    play = Play(id=1, game_id=1, played_at="2024-01-01")
    assign_play_seasons([play], [sample_season])
    assert play.season_id is None


def test_from_dict_defaults():
    season = Season.from_dict({"id": 2})
    assert season.name == ""
    assert season.notes == ""
