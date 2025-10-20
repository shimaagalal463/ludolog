"""Tests for ludolog.io_json."""
import json

import pytest

from ludolog.errors import ImportError as LudologImportError, StorageError
from ludolog.game import Game
from ludolog.io_json import (
    export_library_json,
    export_minimal,
    import_library_json,
    load_partial,
    merge_json_into,
)
from ludolog.play import Play
from ludolog.player import Player


def test_export_library_json_pretty(tmp_journal, tmp_path):
    tmp_journal.add_game(Game(title="Azul"))
    out = tmp_path / "lib.json"
    export_library_json(tmp_journal, out, pretty=True)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["games"][0]["title"] == "Azul"
    assert "\n" in out.read_text(encoding="utf-8")


def test_export_library_json_compact(tmp_journal, tmp_path):
    tmp_journal.add_game(Game(title="Azul"))
    out = tmp_path / "compact.json"
    export_library_json(tmp_journal, out, pretty=False)
    text = out.read_text(encoding="utf-8")
    assert "\n  " not in text


def test_import_library_json_roundtrip(populated_library, tmp_path):
    out = tmp_path / "roundtrip.json"
    export_library_json(populated_library, out)
    loaded = import_library_json(out)
    assert len(loaded.games) == 3
    assert len(loaded.plays) == 1


def test_load_partial_from_v3_fixture(loaded_library):
    path = loaded_library.path
    data = load_partial(path)
    assert data["schema_version"] == 3
    assert data["games"][0]["title"] == "Wingspan"


def test_load_partial_migrates_v0(v0_fixture_data, tmp_path):
    path = tmp_path / "v0.json"
    path.write_text(json.dumps(v0_fixture_data), encoding="utf-8")
    data = load_partial(path)
    assert "schema_version" in data
    assert data["games"][0]["title"] == "Legacy Game"


def test_load_partial_missing_raises(tmp_path):
    with pytest.raises(LudologImportError, match="json not found"):
        load_partial(tmp_path / "missing.json")


def test_load_partial_invalid_json_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(StorageError, match="invalid JSON"):
        load_partial(path)


def test_merge_json_into_adds_new_entities(tmp_journal, loaded_library):
    added = merge_json_into(tmp_journal, loaded_library.path)
    assert added >= 3
    assert any(g.title == "Wingspan" for g in tmp_journal.games)
    assert len(tmp_journal.plays) == 1


def test_merge_json_into_skips_duplicate_game_title(tmp_journal, loaded_library):
    tmp_journal.add_game(Game(title="Wingspan", bgg_id=999))
    added = merge_json_into(tmp_journal, loaded_library.path)
    wingspan = [g for g in tmp_journal.games if g.title == "Wingspan"]
    assert len(wingspan) == 1
    assert wingspan[0].bgg_id == 999


def test_merge_json_into_skips_duplicate_player(tmp_journal, loaded_library):
    tmp_journal.add_player(Player(name="Alex"))
    merge_json_into(tmp_journal, loaded_library.path)
    alex_players = [p for p in tmp_journal.players if p.name == "Alex"]
    assert len(alex_players) == 1


def test_export_minimal_owned_only_and_play_cap(tmp_journal):
    tmp_journal.add_game(Game(title="Owned", owned=True))
    tmp_journal.add_game(Game(title="Wish", owned=False))
    for i in range(105):
        tmp_journal.add_play(
            Play(game_id=1, played_at=f"2025-01-{i % 28 + 1:02d}T12:00:00", player_ids=[])
        )
    out = tmp_journal.path.parent / "minimal.json"
    export_minimal(tmp_journal, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["games"]) == 1
    assert data["games"][0]["title"] == "Owned"
    assert len(data["plays"]) == 100


def test_import_library_json_matches_loaded_fixture(loaded_library):
    lib = import_library_json(loaded_library.path)
    assert lib.games[0].title == "Wingspan"
    assert lib.players[0].name == "Alex"


def test_export_library_json_creates_parent_dir(tmp_journal, tmp_path):
    out = tmp_path / "nested" / "lib.json"
    export_library_json(tmp_journal, out)
    assert out.exists()


def test_merge_json_into_adds_play_records(tmp_journal, tmp_path):
    payload = {
        "schema_version": 3,
        "games": [{"id": 1, "title": "Solo", "owned": True}],
        "plays": [{
            "id": 1,
            "game_id": 1,
            "played_at": "2025-03-01T18:00:00",
            "player_ids": [],
            "winner_ids": [],
        }],
        "players": [],
    }
    path = tmp_path / "partial.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    added = merge_json_into(tmp_journal, path)
    assert added >= 2
    assert len(tmp_journal.plays) == 1


def test_load_partial_v1_fixture(v1_fixture_data, tmp_path):
    path = tmp_path / "v1.json"
    path.write_text(json.dumps(v1_fixture_data), encoding="utf-8")
    data = load_partial(path)
    assert data["schema_version"] >= 1
