"""Tests for ludolog.validators."""
import pytest

from ludolog.errors import ValidationError
from ludolog.game import Game
from ludolog.play import Play
from ludolog.validators import (
    parse_int_list,
    require_non_empty,
    sanitize_notes,
    validate_bgg_id,
    validate_collection_name,
    validate_email,
    validate_game,
    validate_minutes,
    validate_non_negative,
    validate_play,
    validate_player_count,
    validate_port,
    validate_rating,
    validate_schema_version,
    validate_time_hhmm,
    validate_title,
    validate_weekday,
    validate_year,
)


def test_require_non_empty_strips():
    assert require_non_empty("  hello  ", "field") == "hello"


def test_require_non_empty_raises():
    with pytest.raises(ValidationError, match="cannot be empty"):
        require_non_empty("   ", "name")


def test_validate_email_accepts_valid():
    assert validate_email("alice@example.com") == "alice@example.com"


def test_validate_email_rejects_invalid():
    with pytest.raises(ValidationError, match="invalid email"):
        validate_email("not-an-email")


def test_validate_email_allows_blank():
    assert validate_email("  ") == ""


def test_validate_rating_none_and_rounding():
    assert validate_rating(None) is None
    assert validate_rating(8.456) == 8.46


def test_validate_rating_out_of_range():
    with pytest.raises(ValidationError, match="0-10"):
        validate_rating(10.5)


def test_validate_player_count_bounds():
    assert validate_player_count(4) == 4
    with pytest.raises(ValidationError, match="out of range"):
        validate_player_count(0)


def test_validate_minutes_bounds():
    assert validate_minutes(None) is None
    assert validate_minutes(90) == 90
    with pytest.raises(ValidationError, match="unrealistic"):
        validate_minutes(0)


def test_validate_bgg_id_positive():
    assert validate_bgg_id(13) == 13
    assert validate_bgg_id(None) is None
    with pytest.raises(ValidationError, match="positive"):
        validate_bgg_id(0)


def test_validate_year_range():
    assert validate_year(1995) == 1995
    with pytest.raises(ValidationError, match="out of range"):
        validate_year(1800)


def test_parse_int_list_commas_and_semicolons():
    assert parse_int_list("1, 2;3 , 4") == [1, 2, 3, 4]


def test_parse_int_list_rejects_non_integer():
    with pytest.raises(ValidationError, match="not an integer"):
        parse_int_list("1, abc")


def test_validate_title():
    assert validate_title("Catan") == "Catan"
    with pytest.raises(ValidationError):
        validate_title("")


def test_validate_port_range():
    assert validate_port(8080) == 8080
    with pytest.raises(ValidationError, match="port"):
        validate_port(70000)


def test_validate_weekday_truncates():
    assert validate_weekday("Friday") == "fri"
    with pytest.raises(ValidationError, match="weekday"):
        validate_weekday("notaday")


def test_validate_time_hhmm():
    assert validate_time_hhmm("19:30") == "19:30"
    with pytest.raises(ValidationError, match="HH:MM"):
        validate_time_hhmm("25:00")


def test_validate_schema_version():
    assert validate_schema_version(3) == 3
    with pytest.raises(ValidationError, match="schema version"):
        validate_schema_version(99)


def test_validate_non_negative():
    assert validate_non_negative(0.0, "progress") == 0.0
    with pytest.raises(ValidationError, match="non-negative"):
        validate_non_negative(-1.0, "progress")


def test_sanitize_notes_strips_and_truncates():
    long_text = "x" * 5000
    result = sanitize_notes(f"  {long_text}  ", max_len=10)
    assert result == "x" * 10


def test_validate_collection_name_length():
    assert validate_collection_name("Favorites") == "Favorites"
    with pytest.raises(ValidationError, match="too long"):
        validate_collection_name("x" * 121)


def test_validate_play_collects_issues():
    play = Play(id=1, game_id=0, played_at="", duration_minutes=0)
    issues = validate_play(play)
    assert "missing game_id" in issues
    assert "missing played_at" in issues
    assert any("unrealistic" in i for i in issues)


def test_validate_game_collects_issues():
    game = Game(title="", bgg_id=-1, year=1800)
    issues = validate_game(game)
    assert any("title" in i for i in issues)
    assert any("bgg" in i for i in issues)
    assert any("year" in i for i in issues)
