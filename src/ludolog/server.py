"""Read-only HTTP server for library snapshots."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

from .reports import summary_report
from .stats import most_played, player_win_rates

if TYPE_CHECKING:
    from .storage import Library


class LudologHandler(BaseHTTPRequestHandler):
    library: "Library" = None  # type: ignore

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _json(self, code: int, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text(self, code: int, text: str) -> None:
        body = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        lib = self.library
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)

        if path == "/":
            self._text(200, "ludolog server — try /games /plays /stats/summary")
            return
        if path == "/games":
            limit = int(qs.get("limit", ["100"])[0])
            self._json(200, [g.to_dict() for g in lib.games[:limit]])
            return
        if path == "/plays":
            limit = int(qs.get("limit", ["50"])[0])
            self._json(200, [p.to_dict() for p in lib.plays[-limit:]])
            return
        if path == "/players":
            self._json(200, [p.to_dict() for p in lib.players])
            return
        if path == "/stats/summary":
            mp = [{"title": g.title, "count": c} for g, c in most_played(lib, 10)]
            wr = [{"name": n, "rate": r, "played": p} for n, r, p in player_win_rates(lib)]
            self._json(200, {"most_played": mp, "win_rates": wr})
            return
        if path == "/report/summary":
            self._text(200, summary_report(lib))
            return
        self._json(404, {"error": "not found"})


def serve_library(lib: "Library", host: str = "127.0.0.1", port: int = 8765) -> None:
    LudologHandler.library = lib
    server = ThreadingHTTPServer((host, port), LudologHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def make_handler(lib):
    LudologHandler.library = lib
    return LudologHandler


def json_games_subset(lib, fields: list[str] | None = None) -> list[dict]:
    rows = []
    for g in lib.games:
        d = g.to_dict()
        if fields:
            d = {k: d[k] for k in fields if k in d}
        rows.append(d)
    return rows


class LudologServer:
    def __init__(self, lib, host: str = "127.0.0.1", port: int = 8765):
        self.lib = lib
        self.host = host
        self.port = port

    def run(self) -> None:
        serve_library(self.lib, host=self.host, port=self.port)

# TODO: add basic auth for LAN exposure


def handle_path(lib, path: str, query: dict) -> tuple[int, object]:
    if path == "/health":
        from .storage import compute_library_health
        return 200, compute_library_health(lib)
    if path == "/tags":
        from .tags_manager import tag_cloud
        return 200, [{"tag": t, "count": c} for t, c in tag_cloud(lib)]
    if path == "/collections":
        return 200, [c.to_dict() for c in lib.collections]
    if path == "/recurring":
        return 200, [n.to_dict() for n in lib.recurring_nights]
    return 404, {"error": "not found"}
