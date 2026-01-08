#!/usr/bin/env python3
"""Generate JSON test fixtures for ludolog."""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"

GAMES = [
    ("Wingspan", 266192, "engine building"),
    ("Azul", 230802, "pattern building"),
    ("Catan", 13, "negotiation"),
    ("Ticket to Ride", 9209, "route building"),
    ("Pandemic", 30549, "cooperative"),
    ("Splendor", 148228, "engine building"),
    ("Codenames", 178900, "party"),
    ("7 Wonders", 68448, "drafting"),
]


def v0_fixture() -> dict:
    return {"games": [{"id": 1, "title": "Legacy Game", "player_range": {}, "playtime": {}}]}


def v1_fixture() -> dict:
    d = v0_fixture()
    d["schema_version"] = 1
    d["plays"] = []
    d["players"] = [{"id": 1, "name": "Alex"}]
    d["tags"] = ["family"]
    return d


def v3_fixture() -> dict:
    return {
        "schema_version": 3,
        "games": [
            {
                "id": 1,
                "title": "Wingspan",
                "bgg_id": 266192,
                "designer": "Elizabeth Hargrave",
                "player_range": {"min_players": 1, "max_players": 5, "best": 3},
                "playtime": {"min_minutes": 40, "max_minutes": 70},
                "mechanics": ["engine building"],
                "owned": True,
            }
        ],
        "plays": [
            {
                "id": 1,
                "game_id": 1,
                "played_at": "2025-05-01T20:00:00",
                "player_ids": [1],
                "winner_ids": [1],
                "scores": {},
            }
        ],
        "players": [{"id": 1, "name": "Alex", "active": True}],
        "shelves": [],
        "venues": [],
        "notes": [],
        "goals": [],
        "seasons": [],
        "recurring_nights": [],
        "tags": [],
        "collections": [],
        "audit_log": [],
    }


def mega_library(years: int = 7, plays_per_year: int = 400) -> dict:
    rng = random.Random(4242)
    games, plays, players = [], [], []
    for i, (title, bgg, mech) in enumerate(GAMES, start=1):
        games.append(
            {
                "id": i,
                "title": title,
                "bgg_id": bgg,
                "designer": "",
                "player_range": {"min_players": 2, "max_players": 4, "best": 3},
                "playtime": {"min_minutes": 30, "max_minutes": 90},
                "mechanics": [mech],
                "owned": True,
                "tags": [],
            }
        )
    for pid in range(1, 6):
        players.append({"id": pid, "name": f"Player {pid}", "active": True})
    play_id = 0
    start = date(2019, 1, 1)
    for y in range(years):
        for _ in range(plays_per_year):
            play_id += 1
            g = rng.choice(games)
            d = start + timedelta(days=rng.randint(0, 365 * years - 1))
            pids = rng.sample([p["id"] for p in players], k=rng.randint(2, 4))
            winner = rng.choice(pids)
            plays.append(
                {
                    "id": play_id,
                    "game_id": g["id"],
                    "played_at": d.isoformat() + "T19:30:00",
                    "player_ids": pids,
                    "winner_ids": [winner],
                    "scores": {str(w): rng.randint(10, 100) for w in pids},
                    "duration_minutes": rng.randint(30, 120),
                    "venue_id": None,
                    "notes": "",
                    "tags": [],
                }
            )
    return {
        "schema_version": 3,
        "games": games,
        "plays": plays,
        "players": players,
        "shelves": [{"id": 1, "name": "Living room", "game_ids": [g["id"] for g in games[:4]]}],
        "venues": [{"id": 1, "name": "Home table", "kind": "home"}],
        "notes": [],
        "goals": [{"id": 1, "title": "52 unique games", "target_count": 52, "progress": 8}],
        "seasons": [],
        "recurring_nights": [],
        "tags": ["family", "strategy"],
        "collections": [],
        "audit_log": [],
    }


def persona(name: str, owned: int, plays: int) -> dict:
    rng = random.Random(hash(name) & 0xFFFF)
    lib = mega_library(years=3, plays_per_year=plays // 3)
    lib["games"] = lib["games"][:owned]
    lib["plays"] = [p for p in lib["plays"] if p["game_id"] <= owned][:plays]
    return lib


def main() -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    (FIX / "ludolog-v0.json").write_text(json.dumps(v0_fixture(), indent=2), encoding="utf-8")
    (FIX / "ludolog-v1.json").write_text(json.dumps(v1_fixture(), indent=2), encoding="utf-8")
    (FIX / "ludolog-v3.json").write_text(json.dumps(v3_fixture(), indent=2), encoding="utf-8")
    mega = mega_library()
    (FIX / "megalibrary.json").write_text(json.dumps(mega), encoding="utf-8")
    for year in range(2019, 2026):
        subset = dict(mega)
        subset["plays"] = [p for p in mega["plays"] if p["played_at"].startswith(str(year))]
        (FIX / f"ludolog-{year}.json").write_text(json.dumps(subset), encoding="utf-8")
    persona_dir = FIX / "personas"
    persona_dir.mkdir(exist_ok=True)
    for slug, owned, nplays in (
        ("weekend-host", 6, 80),
        ("solo-puzzler", 3, 120),
        ("cafe-regular", 5, 200),
        ("legacy-group", 8, 60),
    ):
        (persona_dir / f"persona-{slug}.json").write_text(
            json.dumps(persona(name=slug, owned=owned, plays=nplays), indent=2),
            encoding="utf-8",
        )
    print("wrote fixtures to", FIX)


if __name__ == "__main__":
    main()
