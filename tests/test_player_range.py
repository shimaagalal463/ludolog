"""Tests for ludolog.player_range."""
import pytest

from ludolog.player_range import (
    PlayerRange,
    best_player_count,
    parse_player_range,
    ranges_overlap,
)


def test_default_player_range_label():
    assert PlayerRange().label() == "?"


def test_fixed_player_count_label():
    pr = PlayerRange(min_players=4, max_players=4)
    assert pr.label() == "4"


def test_range_label_with_best():
    pr = PlayerRange(min_players=2, max_players=5, best=3)
    assert pr.label() == "2-5 (best 3)"


def test_max_only_label():
    pr = PlayerRange(max_players=6)
    assert pr.label() == "1-6"


def test_min_only_label():
    pr = PlayerRange(min_players=3)
    assert pr.label() == "3+"


def test_fits_within_range():
    pr = PlayerRange(min_players=2, max_players=4)
    assert pr.fits(3) is True
    assert pr.fits(1) is False
    assert pr.fits(5) is False


def test_fits_open_range_defaults():
    pr = PlayerRange()
    assert pr.fits(50) is True


def test_to_dict_roundtrip():
    pr = PlayerRange(min_players=1, max_players=5, best=3)
    restored = PlayerRange.from_dict(pr.to_dict())
    assert restored.min_players == 1
    assert restored.max_players == 5
    assert restored.best == 3


def test_parse_range_dash():
    pr = parse_player_range("2-4")
    assert pr.min_players == 2
    assert pr.max_players == 4


def test_parse_single_number():
    pr = parse_player_range("4")
    assert pr.min_players == 4
    assert pr.max_players == 4


def test_parse_plus_suffix():
    pr = parse_player_range("3+")
    assert pr.min_players == 3
    assert pr.max_players is None


def test_parse_with_best():
    pr = parse_player_range("2-5 best 3")
    assert pr.best == 3


def test_parse_empty_string():
    pr = parse_player_range("")
    assert pr.min_players is None


def test_parse_invalid_range():
    pr = parse_player_range("abc-def")
    assert pr.min_players is None


def test_ranges_overlap_true():
    a = PlayerRange(min_players=2, max_players=4)
    b = PlayerRange(min_players=3, max_players=5)
    assert ranges_overlap(a, b) is True


def test_ranges_overlap_false():
    a = PlayerRange(min_players=2, max_players=3)
    b = PlayerRange(min_players=5, max_players=6)
    assert ranges_overlap(a, b) is False


def test_best_player_count_prefers_best():
    pr = PlayerRange(min_players=2, max_players=6, best=4)
    assert best_player_count(pr) == 4


def test_best_player_count_midpoint():
    pr = PlayerRange(min_players=2, max_players=4)
    assert best_player_count(pr) == 3


def test_best_player_count_max_fallback():
    pr = PlayerRange(max_players=5)
    assert best_player_count(pr) == 5


def test_from_dict_missing_keys():
    pr = PlayerRange.from_dict({})
    assert pr.min_players is None
