#!/usr/bin/env python3
"""Bulk import games from CSV then export collection snapshot."""
from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

from ludolog.game import Game
from ludolog.io_csv import export_games_csv
from ludolog.player_range import PlayerRange
from ludolog.playtime import Playtime
from ludolog.storage import init_library


SAMPLE_ROWS = [
    ("Azul", "2-4", "30-45", "pattern building"),
    ("Catan", "3-4", "60-90", "negotiation"),
    ("Ticket to Ride", "2-5", "30-60", "set collection"),
]


def write_sample_csv(dest: Path) -> None:
    with dest.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["title", "players", "minutes", "mechanics"])
        w.writerows(SAMPLE_ROWS)


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp())
    journal = out_dir / "bulk.json"
    csv_path = out_dir / "incoming.csv"
    lib = init_library(journal)
    write_sample_csv(csv_path)
    with csv_path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            pr = PlayerRange()
            if "-" in row["players"]:
                a, b = row["players"].split("-")
                pr = PlayerRange(int(a), int(b))
            pt = Playtime()
            if "-" in row["minutes"]:
                a, b = row["minutes"].split("-")
                pt = Playtime(int(a), int(b))
            mech = [m.strip() for m in row["mechanics"].split(",")]
            lib.add_game(Game(title=row["title"], player_range=pr, playtime=pt, mechanics=mech))
    lib.save()
    export_games_csv(lib, out_dir / "collection.csv")
    print(f"imported {len(lib.games)} games -> {journal}")


if __name__ == "__main__":
    main()
