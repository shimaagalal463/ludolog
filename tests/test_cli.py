"""Tests for ludolog.cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import pytest

from ludolog.cli import (
    build_parser,
    cmd_backup,
    cmd_catalog,
    cmd_export,
    cmd_game_add,
    cmd_health,
    cmd_import,
    cmd_init,
    cmd_migrate,
    cmd_play_add,
    cmd_player_add,
    cmd_report,
    cmd_search,
    cmd_shelf_add,
    cmd_slot,
    cmd_stats,
    cmd_validate,
    cmd_venue_add,
    main,
)
from ludolog.migrate import CURRENT_SCHEMA
from ludolog.storage import Library


def _ns(journal: Path, **kwargs) -> argparse.Namespace:
    return argparse.Namespace(journal=str(journal), **kwargs)


def test_build_parser_registers_init_subcommand():
    parser = build_parser()
    args = parser.parse_args(["init", "journal.json"])
    assert args.cmd == "init"
    assert args.path == "journal.json"
    assert args.func is cmd_init


def test_build_parser_default_journal_is_home_path():
    parser = build_parser()
    args = parser.parse_args(["validate"])
    assert args.journal.endswith("ludolog.json")


def test_main_without_subcommand_prints_help(capsys):
    assert main([]) == 0
    captured = capsys.readouterr()
    assert "ludolog" in captured.out
    assert "init" in captured.out


def test_main_init_creates_journal(tmp_path, capsys):
    path = tmp_path / "new.json"
    assert main(["init", str(path)]) == 0
    captured = capsys.readouterr()
    assert f"initialized {path}" in captured.out
    assert str(CURRENT_SCHEMA) in captured.out
    assert path.exists()


def test_cmd_init_writes_empty_library(tmp_path, capsys):
    path = tmp_path / "lib.json"
    rc = cmd_init(_ns(path, path=str(path)))
    assert rc == 0
    lib = Library.load(path)
    assert lib.games == []
    assert "initialized" in capsys.readouterr().out


def test_cmd_game_add_persists_game(populated_library, capsys):
    before = len(populated_library.games)
    args = _ns(
        populated_library.path,
        title="Azul",
        players="2-4",
        minutes="30-45",
        mechanics="pattern building",
        designer="Michael Kiesling",
        bgg=230802,
    )
    assert cmd_game_add(args) == 0
    lib = Library.load(populated_library.path)
    assert len(lib.games) == before + 1
    assert lib.games[-1].title == "Azul"
    assert "game #" in capsys.readouterr().out


def test_cmd_player_add_persists_player(tmp_journal, capsys):
    args = _ns(tmp_journal.path, name="Carol", handle="carol")
    assert cmd_player_add(args) == 0
    lib = Library.load(tmp_journal.path)
    assert lib.players[0].name == "Carol"
    assert "player #1" in capsys.readouterr().out


def test_cmd_play_add_logs_session(populated_library, capsys):
    before = len(populated_library.plays)
    args = _ns(
        populated_library.path,
        game=1,
        players="Alice, Bob",
        winner="Alice",
        date="2025-06-10",
        duration=80,
        scores=None,
        notes="great game",
        at=None,
    )
    assert cmd_play_add(args) == 0
    lib = Library.load(populated_library.path)
    assert len(lib.plays) == before + 1
    assert lib.plays[-1].duration_minutes == 80
    assert "play #" in capsys.readouterr().out


def test_cmd_play_add_creates_missing_players(tmp_journal, capsys):
    game_args = _ns(
        tmp_journal.path,
        title="Splendor",
        players="2-4",
        minutes="30",
        mechanics="",
        designer="",
        bgg=None,
    )
    cmd_game_add(game_args)
    capsys.readouterr()
    play_args = _ns(
        tmp_journal.path,
        game=1,
        players="Dana",
        winner="",
        date="2025-06-11",
        duration=None,
        scores=None,
        notes="",
        at=None,
    )
    cmd_play_add(play_args)
    lib = Library.load(tmp_journal.path)
    assert len(lib.players) == 1
    assert lib.players[0].name == "Dana"
    assert lib.plays[0].player_ids == [1]


def test_cmd_play_add_scores_infer_winner(tmp_journal, capsys):
    for name in ("Eve", "Frank"):
        cmd_player_add(_ns(tmp_journal.path, name=name, handle=""))
    capsys.readouterr()
    cmd_game_add(
        _ns(
            tmp_journal.path,
            title="7 Wonders",
            players="2-7",
            minutes="30",
            mechanics="",
            designer="",
            bgg=None,
        )
    )
    capsys.readouterr()
    cmd_play_add(
        _ns(
            tmp_journal.path,
            game=1,
            players="Eve, Frank",
            winner="",
            date="2025-06-12",
            duration=None,
            scores="Eve:12,Frank:8",
            notes="",
            at=None,
        )
    )
    lib = Library.load(tmp_journal.path)
    assert lib.plays[0].winner_ids == [1]


def test_cmd_report_summary(populated_library, capsys):
    assert cmd_report(_ns(populated_library.path, kind="summary", days=7, id=1)) == 0
    out = capsys.readouterr().out
    assert "Catan" in out or "games" in out.lower()


def test_cmd_report_player(populated_library, capsys):
    assert cmd_report(_ns(populated_library.path, kind="player", days=7, id=1)) == 0
    out = capsys.readouterr().out
    assert "player: alice" in out
    assert "win rate:" in out


def test_cmd_search_finds_game(populated_library, capsys):
    assert cmd_search(_ns(populated_library.path, query="Catan", limit=10)) == 0
    out = capsys.readouterr().out
    assert "Catan" in out


def test_cmd_slot_lists_matching_games(populated_library, capsys):
    assert cmd_slot(_ns(populated_library.path, minutes=90, players=4, slack=15)) == 0
    out = capsys.readouterr().out
    assert "Catan" in out or "Pandemic" in out


def test_cmd_import_json_merges_fixture(populated_library, capsys):
    fixture = Path(__file__).parent / "fixtures" / "ludolog-v1.json"
    before = len(populated_library.games)
    assert cmd_import(_ns(populated_library.path, format="json", file=str(fixture))) == 0
    lib = Library.load(populated_library.path)
    assert len(lib.games) >= before
    assert "imported" in capsys.readouterr().out


def test_cmd_import_csv_plays(tmp_journal, ludolog_plays_csv_path, capsys):
    assert cmd_import(_ns(tmp_journal.path, format="csv", file=str(ludolog_plays_csv_path))) == 0
    lib = Library.load(tmp_journal.path)
    assert len(lib.plays) > 0
    assert "imported" in capsys.readouterr().out


def test_cmd_export_json(populated_library, tmp_path, capsys):
    dest = tmp_path / "out.json"
    assert cmd_export(_ns(populated_library.path, format="json", dest=str(dest))) == 0
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert len(data["games"]) == len(populated_library.games)
    assert "exported" in capsys.readouterr().out


def test_cmd_export_csv_games(populated_library, tmp_path, capsys):
    dest = tmp_path / "games.csv"
    assert cmd_export(_ns(populated_library.path, format="csv-games", dest=str(dest))) == 0
    text = dest.read_text(encoding="utf-8")
    assert "Catan" in text
    assert "exported" in capsys.readouterr().out


def test_cmd_backup_creates_copy(populated_library, tmp_path, capsys):
    dest = tmp_path / "backups"
    assert cmd_backup(_ns(populated_library.path, dest=str(dest), label="test")) == 0
    backups = list(dest.iterdir())
    assert len(backups) == 1
    assert "backup ->" in capsys.readouterr().out


def test_cmd_migrate_check_reports_plan(tmp_path, capsys):
    src = Path(__file__).parent / "fixtures" / "ludolog-v0.json"
    journal = tmp_path / "v0.json"
    journal.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    assert cmd_migrate(_ns(journal, check=True)) == 0
    assert "needs migrations" in capsys.readouterr().out


def test_cmd_migrate_upgrades_schema(tmp_path, capsys):
    src = Path(__file__).parent / "fixtures" / "ludolog-v0.json"
    journal = tmp_path / "v0.json"
    journal.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    assert cmd_migrate(_ns(journal, check=False)) == 0
    lib = Library.load(journal)
    assert lib.schema_version == CURRENT_SCHEMA
    assert f"at schema {CURRENT_SCHEMA}" in capsys.readouterr().out


def test_cmd_validate_ok_on_populated(populated_library, capsys):
    assert cmd_validate(_ns(populated_library.path)) == 0
    assert capsys.readouterr().out.strip() == "ok"


def test_cmd_stats_summary(populated_library, capsys):
    assert cmd_stats(_ns(populated_library.path, kind="summary", top=10)) == 0
    out = capsys.readouterr().out
    assert "avg players/session" in out
    assert "total minutes logged" in out


def test_cmd_stats_leaderboard(populated_library, capsys):
    assert cmd_stats(_ns(populated_library.path, kind="leaderboard", top=5)) == 0
    out = capsys.readouterr().out
    assert "alice\tw1\tp1" in out


def test_cmd_health_reports_metrics(populated_library, capsys):
    assert cmd_health(_ns(populated_library.path)) == 0
    out = capsys.readouterr().out
    assert "broken_refs: 0" in out
    assert "open_goals: 1" in out


def test_cmd_catalog_stats(populated_library, capsys):
    assert cmd_catalog(_ns(populated_library.path, action="stats")) == 0
    out = capsys.readouterr().out
    assert "total=3" in out
    assert "owned=" in out


def test_cmd_shelf_add(tmp_journal, capsys):
    assert cmd_shelf_add(
        _ns(tmp_journal.path, name="Office", location="Work", capacity=10)
    ) == 0
    lib = Library.load(tmp_journal.path)
    assert lib.shelves[0].name == "Office"
    assert "shelf #1" in capsys.readouterr().out


def test_cmd_venue_add(tmp_journal, capsys):
    assert cmd_venue_add(
        _ns(tmp_journal.path, name="Cafe", address="1 Main", default=True)
    ) == 0
    lib = Library.load(tmp_journal.path)
    assert lib.venues[0].default_for_nights is True
    assert "venue #1" in capsys.readouterr().out


def test_cmd_import_unknown_format_returns_error(populated_library, capsys):
    args = argparse.Namespace(
        journal=str(populated_library.path),
        format="bogus",
        file="x.csv",
    )
    assert cmd_import(args) == 1
    assert "unknown format" in capsys.readouterr().err
