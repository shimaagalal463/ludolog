"""Tests for ludolog.io_bgstats."""
import pytest

from ludolog.errors import ImportError as LudologImportError
from ludolog.io_bgstats import (
    _parse_bgstats_date,
    _parse_duration,
    detect_bgstats_columns,
    import_bgstats_csv,
    import_bgstats_flexible,
    plays_to_bgstats_rows,
)
from ludolog.venue import Venue


def test_import_bgstats_csv_creates_play_and_players(tmp_journal, bgstats_csv_path):
    count = import_bgstats_csv(tmp_journal, bgstats_csv_path)
    assert count == 1
    assert len(tmp_journal.plays) == 1
    assert len(tmp_journal.players) == 2
    assert {p.name for p in tmp_journal.players} == {"Alex", "Sam"}


def test_import_bgstats_csv_creates_game(tmp_journal, bgstats_csv_path):
    import_bgstats_csv(tmp_journal, bgstats_csv_path)
    assert tmp_journal.games[0].title == "Azul"


def test_import_bgstats_csv_sets_winner_and_duration(tmp_journal, bgstats_csv_path):
    import_bgstats_csv(tmp_journal, bgstats_csv_path)
    play = tmp_journal.plays[0]
    assert play.duration_minutes == 40
    winner = next(p for p in tmp_journal.players if p.id in play.winner_ids)
    assert winner.name == "Alex"


def test_import_bgstats_csv_creates_venue(tmp_journal, bgstats_csv_path):
    import_bgstats_csv(tmp_journal, bgstats_csv_path)
    assert tmp_journal.venues[0].name == "Home"
    assert tmp_journal.plays[0].venue_id == tmp_journal.venues[0].id


def test_import_bgstats_csv_missing_file_raises(tmp_journal, tmp_path):
    with pytest.raises(LudologImportError, match="bg stats csv not found"):
        import_bgstats_csv(tmp_journal, tmp_path / "nope.csv")


def test_import_bgstats_csv_reuses_existing_venue(tmp_journal, bgstats_csv_path):
    venue = tmp_journal.add_venue(Venue(name="Home"))
    import_bgstats_csv(tmp_journal, bgstats_csv_path)
    assert len(tmp_journal.venues) == 1
    assert tmp_journal.plays[0].venue_id == venue.id


def test_import_bgstats_flexible(tmp_journal, bgstats_csv_path):
    count = import_bgstats_flexible(tmp_journal, bgstats_csv_path)
    assert count == 1


def test_plays_to_bgstats_rows(populated_library):
    rows = plays_to_bgstats_rows(populated_library)
    assert len(rows) == 1
    assert rows[0]["Game"] == "Catan"
    assert "alice" in rows[0]["Players"].lower()
    assert rows[0]["Duration"] == "75"


def test_detect_bgstats_columns_standard_header():
    mapping = detect_bgstats_columns(["Game", "Date", "Players", "Winner", "Duration", "Location"])
    assert mapping["game"] == "Game"
    assert mapping["date"] == "Date"
    assert mapping["players"] == "Players"
    assert mapping["winner"] == "Winner"
    assert mapping["duration"] == "Duration"
    assert mapping["location"] == "Location"


def test_parse_bgstats_date_iso():
    assert _parse_bgstats_date("2025-05-10") == "2025-05-10T00:00:00"


def test_parse_bgstats_date_slash_format():
    assert _parse_bgstats_date("10/05/2025") == "2025-05-10T00:00:00"


def test_parse_duration_minutes_integer():
    assert _parse_duration("90") == 90


def test_parse_duration_hours_and_minutes():
    assert _parse_duration("1h30") == 90


def test_parse_duration_empty_returns_none():
    assert _parse_duration("") is None


def test_import_bgstats_cooperative_win(tmp_journal, tmp_path):
    path = tmp_path / "coop.csv"
    path.write_text(
        "Game,Date,Players,Winner\n"
        "Pandemic,2025-01-01,\"A,B\",cooperative win\n",
        encoding="utf-8",
    )
    import_bgstats_csv(tmp_journal, path)
    play = tmp_journal.plays[0]
    assert set(play.winner_ids) == set(play.player_ids)
