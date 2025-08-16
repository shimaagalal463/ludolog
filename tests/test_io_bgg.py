"""Tests for ludolog.io_bgg."""
import csv
import json

import pytest

from ludolog.errors import ImportError as LudologImportError
from ludolog.game import Game
from ludolog.io_bgg import (
    export_bgg_compatible_rows,
    import_bgg_csv,
    import_bgg_flexible_csv,
    import_bgg_json,
    map_bgg_headers,
    normalize_bgg_header,
    split_mechanics_field,
    validate_bgg_row,
)


def test_import_bgg_csv_adds_games(tmp_journal, bgg_csv_path):
    count = import_bgg_csv(tmp_journal, bgg_csv_path)
    assert count == 2
    titles = {g.title for g in tmp_journal.games}
    assert titles == {"Azul", "Spirit Island"}


def test_import_bgg_csv_missing_file_raises(tmp_journal, tmp_path):
    with pytest.raises(LudologImportError, match="bgg csv not found"):
        import_bgg_csv(tmp_journal, tmp_path / "missing.csv")


def test_import_bgg_csv_skips_duplicate_title(tmp_journal, bgg_csv_path):
    tmp_journal.add_game(Game(title="Azul", bgg_id=99999))
    count = import_bgg_csv(tmp_journal, bgg_csv_path)
    assert count == 1
    azul = next(g for g in tmp_journal.games if g.title == "Azul")
    assert azul.bgg_id == 99999


def test_import_bgg_csv_merges_existing_bgg_id(tmp_journal, bgg_csv_path):
    tmp_journal.add_game(Game(title="Old Azul", bgg_id=230802))
    count = import_bgg_csv(tmp_journal, bgg_csv_path)
    assert count == 1
    azul = next(g for g in tmp_journal.games if g.bgg_id == 230802)
    assert azul.title == "Old Azul"
    assert len(tmp_journal.games) == 2


def test_import_bgg_json_list_format(tmp_journal, tmp_path):
    path = tmp_path / "bgg.json"
    path.write_text(
        json.dumps([{"name": "Root", "id": 123, "owned": True}]),
        encoding="utf-8",
    )
    count = import_bgg_json(tmp_journal, path)
    assert count == 1
    assert tmp_journal.games[0].title == "Root"
    assert tmp_journal.games[0].bgg_id == 123


def test_import_bgg_json_wrapped_games_key(tmp_journal, tmp_path):
    path = tmp_path / "bgg.json"
    path.write_text(
        json.dumps({"games": [{"title": "Brass", "bgg_id": 55}]}),
        encoding="utf-8",
    )
    count = import_bgg_json(tmp_journal, path)
    assert count == 1
    assert tmp_journal.games[0].title == "Brass"


def test_import_bgg_flexible_csv(tmp_journal, bgg_csv_path):
    count = import_bgg_flexible_csv(tmp_journal, bgg_csv_path)
    assert count == 2


def test_export_bgg_compatible_rows(populated_library):
    rows = export_bgg_compatible_rows(populated_library)
    assert len(rows) == 3
    catan = next(r for r in rows if r["Object name"] == "Catan")
    assert catan["objectid"] == "13"
    assert catan["Own"] == "1"
    assert catan["minplayers"] == "3"


def test_normalize_bgg_header_strips_and_lowercases():
    assert normalize_bgg_header(" Object name ") == "objectname"


def test_map_bgg_headers_normalizes_keys():
    mapped = map_bgg_headers({"Object name": "Azul", "Min Players": "2"})
    assert mapped["objectname"] == "Azul"
    assert mapped["minplayers"] == "2"


def test_validate_bgg_row_valid():
    assert validate_bgg_row({"Object name": "Azul", "objectid": "230802"}) == []


def test_validate_bgg_row_missing_title():
    issues = validate_bgg_row({"objectid": "1"})
    assert "missing title" in issues


def test_validate_bgg_row_invalid_bgg_id():
    issues = validate_bgg_row({"Object name": "X", "objectid": "abc"})
    assert "invalid bgg id" in issues


def test_split_mechanics_field_pipe_separated():
    assert split_mechanics_field("draft|auction|trading") == ["draft", "auction", "trading"]


def test_split_mechanics_field_empty():
    assert split_mechanics_field("") == []


def test_import_bgg_csv_parses_player_counts(tmp_journal, bgg_csv_path):
    import_bgg_csv(tmp_journal, bgg_csv_path)
    azul = next(g for g in tmp_journal.games if g.title == "Azul")
    assert azul.player_range.min_players == 2
    assert azul.player_range.max_players == 4
    assert azul.playtime.max_minutes == 45


def test_import_bgg_csv_wishlist_when_not_owned(tmp_journal, tmp_path):
    path = tmp_path / "wish.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["Object name", "objectid", "Own"],
        )
        writer.writeheader()
        writer.writerow({"Object name": "Wish Game", "objectid": "1", "Own": "0"})
    import_bgg_csv(tmp_journal, path)
    game = tmp_journal.games[0]
    assert game.owned is False
    assert game.wishlist is True


def test_import_bgg_json_nested_player_range(tmp_journal, tmp_path):
    path = tmp_path / "nested.json"
    path.write_text(
        json.dumps([{
            "name": "Nested",
            "player_range": {"min": 2, "max": 5},
            "playtime": {"min": 30, "max": 60},
        }]),
        encoding="utf-8",
    )
    import_bgg_json(tmp_journal, path)
    g = tmp_journal.games[0]
    assert g.player_range.min_players == 2
    assert g.playtime.max_minutes == 60
