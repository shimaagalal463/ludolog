#!/usr/bin/env python3
"""Minimal ludolog tour — run from repo root after pip install -e ."""
from __future__ import annotations

import tempfile
from pathlib import Path

from ludolog.game import Game
from ludolog.play import Play
from ludolog.player import Player
from ludolog.player_range import PlayerRange
from ludolog.playtime import Playtime
from ludolog.stats import games_for_slot, most_played
from ludolog.storage import init_library


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "demo.json"
        lib = init_library(path)
        wingspan = lib.add_game(
            Game(
                title="Wingspan",
                bgg_id=266192,
                designer="Elizabeth Hargrave",
                player_range=PlayerRange(1, 5, best=3),
                playtime=Playtime(40, 70),
                mechanics=["engine building", "set collection"],
            )
        )
        alex = lib.add_player(Player(name="Alex"))
        sam = lib.add_player(Player(name="Sam"))
        lib.add_play(
            Play(
                game_id=wingspan.id,
                played_at="2025-06-01T19:30:00",
                player_ids=[alex.id, sam.id],
                winner_ids=[alex.id],
                duration_minutes=65,
            )
        )
        lib.save()
        print("journal:", path)
        print(most_played(lib, 3))
        picks = games_for_slot(lib, minutes=60, players=2, slack=10)
        print("fits 60min/2p:", [g.title for g in picks])


if __name__ == "__main__":
    main()
