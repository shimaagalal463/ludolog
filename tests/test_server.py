"""Tests for ludolog.server."""
from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from ludolog.server import (
    LudologHandler,
    LudologServer,
    handle_path,
    json_games_subset,
    make_handler,
    serve_library,
)


def _handler_for(lib, path: str = "/") -> LudologHandler:
    LudologHandler.library = lib
    handler = LudologHandler.__new__(LudologHandler)
    handler.path = path
    handler.wfile = BytesIO()
    handler.response_code = None
    handler.response_headers = {}

    def send_response(code, message=None):
        handler.response_code = code

    def send_header(key, value):
        handler.response_headers[key] = value

    def end_headers():
        pass

    handler.send_response = send_response
    handler.send_header = send_header
    handler.end_headers = end_headers
    return handler


def _body(handler: LudologHandler) -> bytes:
    return handler.wfile.getvalue()


def test_handle_path_health(populated_library):
    code, payload = handle_path(populated_library, "/health", {})
    assert code == 200
    assert payload["broken_refs"] == 0
    assert payload["unplayed_owned"] == 1
    assert payload["open_goals"] == 1


def test_handle_path_tags(populated_library):
    code, payload = handle_path(populated_library, "/tags", {})
    assert code == 200
    tags = {row["tag"] for row in payload}
    assert "family" in tags or "classic" in tags


def test_handle_path_collections(populated_library):
    code, payload = handle_path(populated_library, "/collections", {})
    assert code == 200
    assert len(payload) == 1
    assert payload[0]["name"] == "Favorites"


def test_handle_path_recurring(populated_library):
    code, payload = handle_path(populated_library, "/recurring", {})
    assert code == 200
    assert payload[0]["name"] == "Friday Night"


def test_handle_path_not_found(populated_library):
    code, payload = handle_path(populated_library, "/missing", {})
    assert code == 404
    assert payload["error"] == "not found"


def test_json_games_subset_all_fields(populated_library):
    rows = json_games_subset(populated_library)
    assert len(rows) == 3
    assert "title" in rows[0]
    assert rows[0]["title"] == "Catan"


def test_json_games_subset_filtered_fields(populated_library):
    rows = json_games_subset(populated_library, fields=["id", "title"])
    assert rows[0] == {"id": 1, "title": "Catan"}
    assert "mechanics" not in rows[0]


def test_json_games_subset_empty_library(tmp_journal):
    assert json_games_subset(tmp_journal) == []


def test_handler_root_returns_banner(populated_library):
    h = _handler_for(populated_library, "/")
    h.do_GET()
    assert h.response_code == 200
    assert b"ludolog server" in _body(h)


def test_handler_games_returns_json(populated_library):
    h = _handler_for(populated_library, "/games")
    h.do_GET()
    data = json.loads(_body(h).decode("utf-8"))
    assert h.response_code == 200
    assert len(data) == 3
    assert data[0]["title"] == "Catan"


def test_handler_games_respects_limit(populated_library):
    h = _handler_for(populated_library, "/games?limit=1")
    h.do_GET()
    data = json.loads(_body(h).decode("utf-8"))
    assert len(data) == 1


def test_handler_plays_returns_recent(populated_library):
    h = _handler_for(populated_library, "/plays")
    h.do_GET()
    data = json.loads(_body(h).decode("utf-8"))
    assert len(data) == 1
    assert data[0]["game_id"] == 1


def test_handler_players_list(populated_library):
    h = _handler_for(populated_library, "/players")
    h.do_GET()
    data = json.loads(_body(h).decode("utf-8"))
    names = {p["name"] for p in data}
    assert names == {"Alice", "Bob"}


def test_handler_stats_summary(populated_library):
    h = _handler_for(populated_library, "/stats/summary")
    h.do_GET()
    data = json.loads(_body(h).decode("utf-8"))
    assert "most_played" in data
    assert "win_rates" in data
    assert data["most_played"][0]["title"] == "Catan"


def test_handler_report_summary_text(populated_library):
    h = _handler_for(populated_library, "/report/summary")
    h.do_GET()
    assert h.response_code == 200
    assert b"Catan" in _body(h) or b"game" in _body(h).lower()


def test_handler_unknown_path_404(populated_library):
    h = _handler_for(populated_library, "/nope")
    h.do_GET()
    data = json.loads(_body(h).decode("utf-8"))
    assert h.response_code == 404
    assert data["error"] == "not found"


def test_make_handler_binds_library(populated_library):
    cls = make_handler(populated_library)
    assert cls.library is populated_library


def test_ludolog_server_run_delegates(populated_library):
    server = LudologServer(populated_library, host="127.0.0.1", port=9999)
    with patch("ludolog.server.serve_library") as mock_serve:
        server.run()
    mock_serve.assert_called_once_with(populated_library, host="127.0.0.1", port=9999)


def test_serve_library_starts_http_server(populated_library):
    with patch("ludolog.server.ThreadingHTTPServer") as mock_http:
        instance = MagicMock()
        mock_http.return_value = instance
        instance.serve_forever.side_effect = KeyboardInterrupt
        serve_library(populated_library, host="127.0.0.1", port=8765)
    instance.server_close.assert_called_once()
