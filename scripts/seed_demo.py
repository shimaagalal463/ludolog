#!/usr/bin/env python3
"""Seed a demo ludolog journal with sample data."""
from __future__ import annotations

import sys
from pathlib import Path

from ludolog.collections import Collection
from ludolog.game import Game
from ludolog.goal import Goal, GoalKind
from ludolog.play import Play
from ludolog.player import Player
from ludolog.player_range import PlayerRange
from ludolog.playtime import Playtime
from ludolog.recurring import RecurringNight
from ludolog.season import Season
from ludolog.shelf import Shelf
from ludolog.storage import init_library
from ludolog.venue import Venue


def main() -> None:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("demo-ludolog.json")
    lib = init_library(dest)
    shelf = lib.add_shelf(Shelf(name="Living room Kallax", location="Living room", capacity=40))
    venue = lib.add_venue(Venue(name="Home table", default_for_nights=True))
    alex = lib.add_player(Player(name="Alex", handle="alex"))
    sam = lib.add_player(Player(name="Sam"))
    jordan = lib.add_player(Player(name="Jordan"))
    games = [
        Game(title="Wingspan", bgg_id=266192, player_range=PlayerRange(1, 5, 3), playtime=Playtime(40, 70), mechanics=["engine building"], shelf_id=shelf.id),
        Game(title="Azul", bgg_id=230802, player_range=PlayerRange(2, 4), playtime=Playtime(30, 45), mechanics=["pattern building"], shelf_id=shelf.id),
        Game(title="Spirit Island", bgg_id=162886, player_range=PlayerRange(1, 4), playtime=Playtime(90, 120), mechanics=["cooperative", "hand management"]),
    ]
    for g in games:
        lib.add_game(g)
    lib.add_play(Play(game_id=1, played_at="2025-05-20T19:00:00", player_ids=[alex.id, sam.id], winner_ids=[alex.id], duration_minutes=68, venue_id=venue.id))
    lib.add_play(Play(game_id=2, played_at="2025-05-22T20:00:00", player_ids=[alex.id, sam.id, jordan.id], winner_ids=[sam.id], duration_minutes=40, venue_id=venue.id))
    lib.add_collection(Collection(name="Weeknight fillers", game_ids=[2], pinned=True))
    lib.add_goal(Goal(kind=GoalKind.PLAY_COUNT.value, title="Play Wingspan 5 times", target=5, game_id=1))
    lib.seasons.append(Season(id=1, name="2025", start_date="2025-01-01", end_date="2025-12-31"))
    lib.recurring_nights.append(RecurringNight(id=1, name="Friday games", weekday="fri", default_venue_id=venue.id, usual_player_ids=[alex.id, sam.id]))
    lib.save()
    print(f"seeded {dest} — {len(lib.games)} games, {len(lib.plays)} plays")


if __name__ == "__main__":
    main()
