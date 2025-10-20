"""Tests for ludolog.parser."""
from __future__ import annotations

from ludolog.parser import (
    parse_bool,
    parse_duration_arg,
    parse_game_fields,
    parse_key_values,
    parse_score_pairs,
    parse_tags,
    split_names,
)
from ludolog.player_range import PlayerRange
from ludolog.playtime import Playtime


def test_parse_key_values_basic():
    result = parse_key_values("title=Catan, players=3-4")
    assert result == {"title": "Catan", "players": "3-4"}


def test_parse_key_values_skips_invalid_chunks():
    result = parse_key_values("title=Catan, broken, rating=8")
    assert "title" in result
    assert "rating" in result
    assert len(result) == 2


def test_parse_key_values_lowercases_keys():
    result = parse_key_values("Title=Catan, RATING=8.5")
    assert result["title"] == "Catan"
    assert result["rating"] == "8.5"


def test_parse_score_pairs_valid():
    scores = parse_score_pairs("Alice:10, Bob:7.5")
    assert scores == {"Alice": 10.0, "Bob": 7.5}


def test_parse_score_pairs_skips_invalid_float():
    scores = parse_score_pairs("Alice:ten, Bob:5")
    assert scores == {"Bob": 5.0}


def test_parse_score_pairs_skips_no_colon():
    scores = parse_score_pairs("Alice-10, Bob:5")
    assert scores == {"Bob": 5.0}


def test_parse_tags_splits_and_lowercases():
    tags = parse_tags("Family, Co-Op , classic")
    assert tags == ["family", "co-op", "classic"]


def test_parse_tags_empty_segments():
    assert parse_tags(", , ") == []


def test_parse_game_fields_full():
    title, pr, pt, mech = parse_game_fields(
        "  Catan  ", "3-4", "60-90", "Trading, Dice Rolling"
    )
    assert title == "Catan"
    assert isinstance(pr, PlayerRange)
    assert pr.min_players == 3
    assert isinstance(pt, Playtime)
    assert pt.max_minutes == 90
    assert mech == ["Trading", "Dice Rolling"]


def test_parse_game_fields_empty_optional():
    title, pr, pt, mech = parse_game_fields("Azul")
    assert title == "Azul"
    assert pr.min_players is None
    assert pt.min_minutes is None
    assert mech == []


def test_split_names_comma():
    assert split_names("Alice, Bob, Carol") == ["Alice", "Bob", "Carol"]


def test_split_names_semicolon():
    assert split_names("Alice; Bob") == ["Alice", "Bob"]


def test_split_names_strips_whitespace():
    assert split_names("  Alice ,  ") == ["Alice"]


def test_parse_duration_arg_digits():
    assert parse_duration_arg("90") == 90


def test_parse_duration_arg_hours():
    assert parse_duration_arg("1.5h") == 90


def test_parse_duration_arg_empty():
    assert parse_duration_arg("") is None
    assert parse_duration_arg("   ") is None


def test_parse_duration_arg_invalid():
    assert parse_duration_arg("abc") is None
    assert parse_duration_arg("xh") is None


def test_parse_bool_true_variants():
    for val in ("1", "true", "yes", "y", "on", " TRUE "):
        assert parse_bool(val) is True


def test_parse_bool_false_variants():
    for val in ("0", "false", "no", "off", ""):
        assert parse_bool(val) is False
