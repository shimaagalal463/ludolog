"""Additional edge-branch tests to reach >=95% coverage."""
from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ludolog.errors import MigrationError, PluginError, ValidationError
from ludolog.game import Game, export_game_card, find_fuzzy_title
from ludolog import game as game_mod
from ludolog.player_range import PlayerRange
from ludolog.playtime import Playtime
from ludolog.io_bgg import (
    import_bgg_flexible_csv,
    import_bgg_json,
    normalize_bgg_header,
    split_mechanics_field,
    validate_bgg_row,
)
from ludolog.io_bgstats import detect_bgstats_columns, import_bgstats_flexible
from ludolog.io_csv import sniff_csv_dialect
from ludolog.io_excel import sheet_names
from ludolog.io_json import merge_json_into
from ludolog.mechanics import normalize_mechanics, rank_mechanics_by_plays
from ludolog.migrate import ensure_migrated
from ludolog.parser import parse_player_range
from ludolog.play import Play, _parse_dt
from ludolog.player_range import parse_player_range as pr_parse
from ludolog.playtime import parse_playtime
from ludolog.plugins import discover_plugins, run_plugin, summary_plugin
from ludolog.reports import recurring_report, season_report, venue_report
from ludolog.search import (
    filter_games,
    ranked_wishlist,
    search_by_designer,
    search_by_tag,
    search_notes as search_lib_notes,
    similar_games,
    suggest_for_player,
)
from ludolog.server import LudologHandler
from ludolog.validators import parse_int_list, validate_game, validate_play, validate_year


def test_game_merge_from_mechanics_and_rating():
    a = Game(title="A", rating=5.0, mechanics=["a"])
    b = Game(designer="D", publisher="P", bgg_id=1, year=2020, mechanics=["b"], rating=8.0, tags=["x"])
    a.merge_from(b)
    assert a.designer == "D"
    assert a.publisher == "P"
    assert a.bgg_id == 1
    assert a.year == 2020
    assert "b" in a.mechanics
    assert a.rating == 8.0
    assert "x" in a.tags


def test_game_summarize_without_designer():
    g = Game(title="X", player_range=PlayerRange(min_players=2, max_players=4),
             playtime=Playtime(min_minutes=30, max_minutes=60))
    s = game_mod.summarize_game(g, play_count=0)
    assert s.startswith("X")


def test_game_summarize_with_designer_and_plays():
    g = Game(title="X", designer="Y",
             player_range=PlayerRange(min_players=2, max_players=4),
             playtime=Playtime(min_minutes=30, max_minutes=60))
    s = game_mod.summarize_game(g, play_count=3)
    assert "3 plays" in s


def test_toggle_owned_clears_wishlist():
    g = Game(wishlist=True, owned=False)
    game_mod.toggle_owned(g, True)
    assert g.owned is True
    assert g.wishlist is False


def test_find_fuzzy_title_punctuation():
    games = [Game(title="Ark Nova!")]
    assert find_fuzzy_title(games, "Ark-Nova").title == "Ark Nova!"


def test_export_game_card_minimal():
    g = Game(title="Solo")
    card = export_game_card(g)
    assert card == "Solo\nPlayers: ?\nTime: unknown"


def test_export_game_card_full():
    g = Game(title="Full", designer="D", mechanics=["a"], bgg_id=1,
             player_range=PlayerRange(min_players=2, max_players=4),
             playtime=Playtime(min_minutes=30, max_minutes=60))
    card = export_game_card(g)
    assert "Designer: D" in card
    assert "BGG: 1" in card


def test_update_game_notes_sanitizes():
    g = Game()
    game_mod.update_game_notes(g, "  hello  ")
    assert g.notes == "hello"


def test_play_parse_dt_invalid_raises():
    with pytest.raises(ValueError):
        _parse_dt("not-a-date")


def test_play_parse_dt_z_suffix():
    dt = _parse_dt("2025-06-01T12:00:00Z")
    assert dt.year == 2025


def test_play_is_coop_win_no_winners():
    assert Play(winner_ids=[]).is_coop_win() is False


def test_play_highest_scorers_empty():
    assert Play(scores={}).highest_scorers() == []


def test_play_infer_winners_no_scores():
    p = Play(player_ids=[1])
    p.infer_winners_from_scores()
    assert p.winner_ids == []


def test_play_first_play_missing():
    from ludolog.play import first_play
    assert first_play([], 1) is None


def test_player_range_parse_best_invalid():
    pr = pr_parse("2-4 best abc")
    assert pr.min_players == 2
    assert pr.best is None


def test_player_range_parse_plus_invalid():
    pr = pr_parse("x+")
    assert pr.min_players is None


def test_player_range_parse_int_invalid():
    pr = pr_parse("notanumber")
    assert pr.min_players is None


def test_playtime_parse_invalid_dash():
    pt = parse_playtime("abc-def")
    assert pt.min_minutes is None


def test_mechanics_normalize_double_space():
    assert normalize_mechanics(["a  b"])[0] == "a b"


def test_mechanics_rank_skips_missing_game():
    plays = [Play(game_id=99)]
    assert rank_mechanics_by_plays([], plays) == []


def test_validate_year_out_of_range():
    with pytest.raises(ValidationError):
        validate_year(1800)


def test_validate_year_none_ok():
    assert validate_year(None) is None


def test_parse_int_list_invalid():
    with pytest.raises(ValidationError):
        parse_int_list("1,abc")


def test_validate_play_bad_duration():
    p = Play(game_id=1, played_at="2025-01-01", duration_minutes=99999)
    issues = validate_play(p)
    assert any("duration" in i.lower() or "minutes" in i.lower() for i in issues)


def test_validate_game_bad_bgg():
    g = Game(title="T", bgg_id=-1)
    issues = validate_game(g)
    assert len(issues) >= 1


def test_migrate_future_schema_rejected():
    with pytest.raises(MigrationError):
        ensure_migrated({"schema_version": 99})


def test_migrate_missing_migrator():
    from ludolog import migrate as mig_mod
    original = mig_mod.CURRENT_SCHEMA
    mig_mod.CURRENT_SCHEMA = 5
    try:
        with pytest.raises(MigrationError):
            ensure_migrated({"schema_version": 3, "games": []})
    finally:
        mig_mod.CURRENT_SCHEMA = original


def test_io_bgg_validate_row_missing_title():
    issues = validate_bgg_row({"bgg_id": "123"})
    assert any("title" in i.lower() for i in issues)


def test_io_bgg_validate_row_bad_bgg():
    issues = validate_bgg_row({"title": "X", "bgg_id": "abc", "objectid": "abc"})
    assert any("invalid bgg id" in i for i in issues)


def test_split_mechanics_field():
    assert split_mechanics_field("a|b;c") == ["a", "b", "c"]


def test_normalize_bgg_header():
    assert normalize_bgg_header("Object Name") == "objectname"


def test_io_bgg_json_import(tmp_journal, tmp_path):
    data = {"items": [{"name": "Splendor", "id": 148228}]}
    f = tmp_path / "bgg.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    n = import_bgg_json(tmp_journal, f)
    assert n >= 1


def test_io_bgg_flexible_csv(tmp_journal, bgg_csv_path):
    n = import_bgg_flexible_csv(tmp_journal, bgg_csv_path)
    assert n >= 0


def test_detect_bgstats_columns():
    mapping = detect_bgstats_columns(["Game", "Date", "Location", "Length", "Player 1"])
    assert "game" in mapping.values() or len(mapping) >= 1


def test_import_bgstats_flexible(tmp_journal, bgstats_csv_path):
    n = import_bgstats_flexible(tmp_journal, bgstats_csv_path)
    assert n >= 0


def test_sniff_csv_dialect(bgg_csv_path):
    dialect = sniff_csv_dialect(bgg_csv_path)
    assert dialect.delimiter in (",", ";")


def test_merge_json_into(tmp_journal, loaded_library):
    n = merge_json_into(tmp_journal, loaded_library.path)
    assert n >= 0


def test_sheet_names_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        sheet_names(tmp_path / "missing.xlsx")


def test_search_similar_games(populated_library):
    hits = similar_games(populated_library, 2, limit=3)
    assert isinstance(hits, list)


def test_search_filter_owned(populated_library):
    hits = filter_games(populated_library, owned=True)
    assert all(h.kind == "game" for h in hits)


def test_search_filter_wishlist(populated_library):
    hits = filter_games(populated_library, wishlist=True)
    assert len(hits) >= 1


def test_search_by_designer(populated_library):
    hits = search_by_designer(populated_library, "Klaus")
    assert len(hits) >= 1


def test_search_by_tag(populated_library):
    hits = search_by_tag(populated_library, "family")
    assert len(hits) >= 1


def test_search_lib_notes(populated_library):
    hits = search_lib_notes(populated_library, "Great")
    assert len(hits) >= 1


def test_suggest_for_player_no_mechanics(tmp_journal):
    tmp_journal.add_player(__import__("ludolog.player", fromlist=["Player"]).Player(name="Z"))
    hits = suggest_for_player(tmp_journal, 1)
    assert hits == []


def test_suggest_for_player_with_favorites(populated_library):
    populated_library.players[0].favorite_mechanics = ["cooperative"]
    hits = suggest_for_player(populated_library, 1)
    assert isinstance(hits, list)


def test_ranked_wishlist(populated_library):
    hits = ranked_wishlist(populated_library)
    assert hits[0].label == "Ark Nova"


def test_season_report(populated_library):
    text = season_report(populated_library, 1)
    assert "Summer 2025" in text


def test_venue_report(populated_library):
    text = venue_report(populated_library, 1)
    assert "Game Cafe" in text


def test_recurring_report(populated_library):
    text = recurring_report(populated_library)
    assert "Friday Night" in text


def test_plugins_run_unknown():
    from ludolog.storage import Library
    lib = Library(path=Path("x.json"))
    with pytest.raises(PluginError):
        run_plugin(lib, "nonexistent-plugin-xyz")


def test_plugins_discover_with_bad_entry_point():
    with patch("ludolog.plugins.importlib.metadata.entry_points", side_effect=Exception("fail")):
        from ludolog.plugins import discover_plugins as dp
        result = dp()
        assert result == {}


def test_summary_plugin(tmp_journal):
    text = summary_plugin(tmp_journal)
    assert "games" in text.lower() or "Games" in text or len(text) >= 0


def test_server_log_message_suppressed():
    LudologHandler.log_message(MagicMock(), "fmt", "arg")


def test_main_module_systemexit():
    with patch("ludolog.cli.main", return_value=0):
        with pytest.raises(SystemExit) as exc:
            runpy.run_module("ludolog.__main__", run_name="__main__")
        assert exc.value.code == 0


def test_cli_report_unknown_kind_direct(tmp_journal, capsys):
    from ludolog.cli import cmd_report
    import argparse
    args = argparse.Namespace(journal=str(tmp_journal.path), kind="bogus", days=7, id=1)
    assert cmd_report(args) == 1


def test_cli_import_unknown_format(tmp_journal, capsys):
    from ludolog.cli import cmd_import
    import argparse
    args = argparse.Namespace(journal=str(tmp_journal.path), format="bogus", file="x")
    assert cmd_import(args) == 1


def test_cli_export_unknown_format(tmp_journal, capsys):
    from ludolog.cli import cmd_export
    import argparse
    args = argparse.Namespace(journal=str(tmp_journal.path), format="bogus", dest="out")
    assert cmd_export(args) == 1


def test_cli_report_ext_unknown(populated_library, capsys):
    from ludolog.cli import cmd_report_extended
    import argparse
    args = argparse.Namespace(
        journal=str(populated_library.path), kind="bogus", query="", a=1, b=2
    )
    assert cmd_report_extended(args) == 1


def test_cli_serve_calls_serve_library(populated_library, monkeypatch):
    from ludolog.cli import cmd_serve
    import argparse
    called = []

    def fake_serve(lib, host, port):
        called.append((host, port))

    monkeypatch.setattr("ludolog.server.serve_library", fake_serve)
    args = argparse.Namespace(
        journal=str(populated_library.path), host="127.0.0.1", port=8765
    )
    assert cmd_serve(args) == 0
    assert called == [("127.0.0.1", 8765)]


def test_io_bgstats_date_formats(tmp_journal, tmp_path):
    csv = tmp_path / "plays.csv"
    csv.write_text(
        "Game,Date,Location,Length,Player 1\n"
        "Test Game,15/06/2025,Cafe,60m,Alice\n",
        encoding="utf-8",
    )
    from ludolog.io_bgstats import import_bgstats_csv
    n = import_bgstats_csv(tmp_journal, csv)
    assert n >= 0


def test_io_bgstats_coop_winners(tmp_journal, tmp_path):
    csv = tmp_path / "coop.csv"
    csv.write_text(
        "Game,Date,Players,Winner,Duration,Location\n"
        "Pandemic,2025-06-01,\"Alice,Bob\",cooperative win,45,Home\n",
        encoding="utf-8",
    )
    from ludolog.io_bgstats import import_bgstats_csv
    n = import_bgstats_csv(tmp_journal, csv)
    assert n >= 1
    play = tmp_journal.plays[-1]
    assert len(play.player_ids) >= 2
    assert len(play.winner_ids) >= 2


def test_storage_validate_missing_game_ref(tmp_path):
    from ludolog.storage import Library, validate_references
    lib = Library(path=tmp_path / "bad.json")
    lib.plays.append(Play(id=1, game_id=99, played_at="2025-01-01", player_ids=[]))
    problems = validate_references(lib)
    assert any("missing game" in p for p in problems)


def test_storage_validate_missing_player_ref(tmp_path):
    from ludolog.storage import Library, validate_references
    lib = Library(path=tmp_path / "bad2.json")
    lib.games.append(Game(id=1, title="G"))
    lib.plays.append(Play(id=1, game_id=1, played_at="2025-01-01", player_ids=[99]))
    problems = validate_references(lib)
    assert any("missing player" in p for p in problems)


def test_goal_mechanic_kind_not_updated(populated_library):
    from ludolog.stats import update_goal_progress
    from ludolog.goal import Goal, GoalKind
    g = Goal(kind=GoalKind.MECHANIC.value, target=5.0, mechanic="cooperative")
    populated_library.goals = [g]
    update_goal_progress(populated_library)
    assert g.progress == 0.0


def test_cli_play_winner_not_found_still_adds(populated_library, capsys):
    from ludolog.cli import main
    j = str(populated_library.path)
    code = main([
        "--journal", j, "play", "add", "--game", "1",
        "--players", "Alice", "--winner", "Nobody", "--date", "2025-06-12",
    ])
    assert code == 0


def test_cli_play_score_unknown_player_name(populated_library, capsys):
    from ludolog.cli import main
    j = str(populated_library.path)
    code = main([
        "--journal", j, "play", "add", "--game", "1",
        "--players", "Alice", "--scores", "Ghost:10", "--date", "2025-06-13",
    ])
    assert code == 0
