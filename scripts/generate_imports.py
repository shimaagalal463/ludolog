#!/usr/bin/env python3
"""Generate sample import CSV files for tests."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "imports"


def write_bgg(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Object name", "objectid", "minplayers", "maxplayers", "minplaytime", "maxplaytime", "Own"])
        w.writerow(["Azul", "230802", "2", "4", "30", "45", "1"])
        w.writerow(["Spirit Island", "162886", "1", "4", "90", "120", "1"])


def write_bgstats(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Game", "Date", "Players", "Winner", "Duration", "Location"])
        w.writerow(["Azul", "2025-05-10", "Alex,Sam", "Alex", "40", "Home"])


def write_plays(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["played_at", "game_title", "players", "winners", "duration", "notes"])
        w.writerow(["2025-05-11T19:00:00", "Azul", "Alex,Sam", "Sam", "35", "close game"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_bgg(OUT / "bgg_collection.csv")
    write_bgstats(OUT / "bgstats_plays.csv")
    write_plays(OUT / "ludolog_plays.csv")
    print("wrote imports to", OUT)


if __name__ == "__main__":
    main()
