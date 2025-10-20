"""Tests for ludolog.io_csv."""
import csv

import pytest

from ludolog.errors import ImportError as LudologImportError
from ludolog.io_csv import (
    export_games_csv,
    export_players_csv,
    export_plays_csv,
    import_games_csv,
    import_plays_csv,
    sniff_csv_dialect,
)


def test_export_plays_csv_writes_rows(populated_library, tmp_path):
    out = tmp_path / "plays.csv"
    count = export_plays_csv(populated_library, out)
    assert count == 1
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert rows[0]["game_title"] == "Catan"
    assert "alice" in rows[0]["players"]
    assert rows[0]["duration"] == "75"


def test_import_plays_csv_from_fixture(tmp_journal, ludolog_plays_csv_path):
    count = import_plays_csv(tmp_journal, ludolog_plays_csv_path)
    assert count == 1
    assert tmp_journal.games[0].title == "Azul"
    assert len(tmp_journal.players) == 2
    play = tmp_journal.plays[0]
    assert play.duration_minutes == 35
    winner = next(p for p in tmp_journal.players if p.id in play.winner_ids)
    assert winner.name == "Sam"


def test_import_plays_csv_missing_file_raises(tmp_journal, tmp_path):
    with pytest.raises(LudologImportError, match="csv not found"):
        import_plays_csv(tmp_journal, tmp_path / "missing.csv")


def test_import_plays_csv_reuses_existing_game(tmp_journal, ludolog_plays_csv_path):
    from ludolog.game import Game
    tmp_journal.add_game(Game(title="Azul"))
    count = import_plays_csv(tmp_journal, ludolog_plays_csv_path)
    assert count == 1
    assert len(tmp_journal.games) == 1


def test_export_games_csv(populated_library, tmp_path):
    out = tmp_path / "games.csv"
    count = export_games_csv(populated_library, out)
    assert count == 3
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    catan = next(r for r in rows if r["title"] == "Catan")
    assert catan["bgg_id"] == "13"
    assert catan["owned"] == "yes"
    assert "trading" in catan["mechanics"]


def test_import_games_csv(tmp_path, tmp_journal):
    path = tmp_path / "games.csv"
    path.write_text(
        "title,players,minutes,mechanics\n"
        "Brass,2-4,60-120,auction|economic\n",
        encoding="utf-8",
    )
    count = import_games_csv(tmp_journal, path)
    assert count == 1
    g = tmp_journal.games[0]
    assert g.title == "Brass"
    assert g.player_range.min_players == 2
    assert g.playtime.max_minutes == 120
    assert "auction" in g.mechanics


def test_import_games_csv_skips_duplicate_title(tmp_journal, tmp_path):
    from ludolog.game import Game
    tmp_journal.add_game(Game(title="Brass"))
    path = tmp_path / "games.csv"
    path.write_text("title\nBrass\n", encoding="utf-8")
    assert import_games_csv(tmp_journal, path) == 0


def test_sniff_csv_dialect_comma(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    dialect = sniff_csv_dialect(path)
    assert dialect.delimiter == ","


def test_sniff_csv_dialect_fallback_on_invalid(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("", encoding="utf-8")
    dialect = sniff_csv_dialect(path)
    assert dialect.delimiter == ","


def test_export_players_csv(populated_library, tmp_path):
    out = tmp_path / "players.csv"
    count = export_players_csv(populated_library, out)
    assert count == 2
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    alice = next(r for r in rows if r["name"] == "Alice")
    assert alice["handle"] == "alice"
    assert alice["active"] == "yes"


def test_import_plays_csv_stores_notes(tmp_journal, tmp_path):
    path = tmp_path / "notes.csv"
    path.write_text(
        "played_at,game_title,players,winners,duration,notes\n"
        "2025-01-01T12:00:00,Test,\"A\",\"A\",30,memorable\n",
        encoding="utf-8",
    )
    import_plays_csv(tmp_journal, path)
    assert tmp_journal.plays[0].notes == "memorable"


def test_import_plays_csv_skips_blank_title(tmp_journal, tmp_path):
    path = tmp_path / "blank.csv"
    path.write_text(
        "played_at,game_title,players\n"
        "2025-01-01,,\"A\"\n",
        encoding="utf-8",
    )
    assert import_plays_csv(tmp_journal, path) == 0


def test_export_plays_roundtrip(populated_library, tmp_path, tmp_journal):
    out = tmp_path / "roundtrip.csv"
    export_plays_csv(populated_library, out)
    import_plays_csv(tmp_journal, out)
    assert len(tmp_journal.plays) == 1
    assert tmp_journal.plays[0].game_id == 1


def test_export_games_includes_wishlist_as_not_owned(populated_library, tmp_path):
    out = tmp_path / "games.csv"
    export_games_csv(populated_library, out)
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    ark = next(r for r in rows if r["title"] == "Ark Nova")
    assert ark["owned"] == "no"


def test_import_plays_csv_creates_players_on_demand(tmp_journal, tmp_path):
    path = tmp_path / "new_players.csv"
    path.write_text(
        "game_title,players,winners\n"
        "G,\"Zoe,Mia\",Zoe\n",
        encoding="utf-8",
    )
    import_plays_csv(tmp_journal, path)
    assert {p.name for p in tmp_journal.players} == {"Zoe", "Mia"}


def test_import_games_csv_skips_empty_title(tmp_journal, tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("title\n\n", encoding="utf-8")
    assert import_games_csv(tmp_journal, path) == 0


def test_export_plays_csv_player_display_names(populated_library, tmp_path):
    out = tmp_path / "display.csv"
    export_plays_csv(populated_library, out)
    text = out.read_text(encoding="utf-8")
    assert "alice" in text
    assert "bob" in text
