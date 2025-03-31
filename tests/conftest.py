"""Shared pytest fixtures for ludolog."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ludolog.collections import Collection
from ludolog.game import Game
from ludolog.goal import Goal, GoalKind
from ludolog.note import Note
from ludolog.play import Play
from ludolog.player import Player
from ludolog.player_range import PlayerRange
from ludolog.playtime import Playtime
from ludolog.recurring import RecurringNight
from ludolog.season import Season
from ludolog.shelf import Shelf
from ludolog.storage import Library, init_library
from ludolog.venue import Venue

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def tmp_journal(tmp_path):
    path = tmp_path / "ludolog.json"
    return init_library(path)


@pytest.fixture
def sample_game():
    return Game(
        title="Catan",
        id=1,
        bgg_id=13,
        designer="Klaus Teuber",
        publisher="Kosmos",
        year=1995,
        player_range=PlayerRange(min_players=3, max_players=4, best=4),
        playtime=Playtime(min_minutes=45, max_minutes=90),
        mechanics=["negotiation", "dice rolling"],
        tags=["classic"],
        rating=8.0,
        owned=True,
    )


@pytest.fixture
def sample_game2():
    return Game(
        title="Pandemic",
        bgg_id=30549,
        designer="Matt Leacock",
        player_range=PlayerRange(min_players=2, max_players=4, best=4),
        playtime=Playtime(min_minutes=30, max_minutes=45),
        mechanics=["cooperative"],
        owned=True,
    )


@pytest.fixture
def sample_game_wishlist():
    return Game(
        title="Ark Nova",
        bgg_id=342942,
        designer="Mathias Wigge",
        year=2021,
        player_range=PlayerRange(min_players=1, max_players=4, best=2),
        playtime=Playtime(min_minutes=90, max_minutes=150),
        mechanics=["engine building"],
        rating=9.5,
        owned=False,
        wishlist=True,
    )


@pytest.fixture
def sample_player():
    return Player(id=1, name="Alice", handle="alice")


@pytest.fixture
def sample_player2():
    return Player(id=2, name="Bob", handle="bob")


@pytest.fixture
def sample_play():
    return Play(
        game_id=1,
        played_at="2025-06-01T19:30:00",
        duration_minutes=75,
        player_ids=[1, 2],
        winner_ids=[1],
        scores={"1": 10.0, "2": 7.0},
        venue_id=1,
    )


@pytest.fixture
def sample_play_incomplete():
    return Play(
        game_id=1,
        played_at="2025-06-02T20:00:00",
        player_ids=[1, 2],
        incomplete=True,
    )


@pytest.fixture
def sample_shelf():
    return Shelf(id=1, name="Living Room", location="Home", capacity=20)


@pytest.fixture
def sample_venue():
    return Venue(
        id=1,
        name="Game Cafe",
        address="123 Main St",
        default_for_nights=True,
    )


@pytest.fixture
def sample_season():
    return Season(
        id=1,
        name="Summer 2025",
        start_date="2025-06-01",
        end_date="2025-08-31",
    )


@pytest.fixture
def sample_recurring():
    return RecurringNight(
        id=1,
        name="Friday Night",
        weekday="fri",
        usual_player_ids=[1],
        preferred_game_ids=[1],
        active=True,
    )


@pytest.fixture
def sample_goal():
    return Goal(
        id=1,
        kind=GoalKind.PLAY_COUNT.value,
        title="Play Catan 5x",
        target=5.0,
        progress=1.0,
        game_id=1,
    )


@pytest.fixture
def sample_note():
    return Note(
        id=1,
        game_id=1,
        body="Great session!",
        created_at="2025-06-01T21:00:00",
    )


@pytest.fixture
def sample_collection():
    return Collection(id=1, name="Favorites", game_ids=[1], pinned=True)


@pytest.fixture
def populated_library(tmp_path):
    path = tmp_path / "populated.json"
    lib = init_library(path)

    catan = Game(
        id=1,
        title="Catan",
        bgg_id=13,
        designer="Klaus Teuber",
        publisher="Kosmos",
        player_range=PlayerRange(min_players=3, max_players=4, best=4),
        playtime=Playtime(min_minutes=45, max_minutes=90),
        mechanics=["trading"],
        tags=["classic", "family"],
        shelf_id=1,
        rating=8.0,
        owned=True,
    )
    pandemic = Game(
        id=2,
        title="Pandemic",
        bgg_id=30549,
        designer="Matt Leacock",
        publisher="Z-Man Games",
        player_range=PlayerRange(min_players=2, max_players=4, best=4),
        playtime=Playtime(min_minutes=30, max_minutes=45),
        mechanics=["cooperative"],
        owned=True,
    )
    ark = Game(
        id=3,
        title="Ark Nova",
        bgg_id=342942,
        designer="Mathias Wigge",
        player_range=PlayerRange(min_players=1, max_players=4, best=2),
        playtime=Playtime(min_minutes=90, max_minutes=150),
        mechanics=["engine building"],
        rating=9.0,
        owned=False,
        wishlist=True,
    )
    lib.games = [catan, pandemic, ark]

    alice = Player(id=1, name="Alice", handle="alice")
    bob = Player(id=2, name="Bob", handle="bob")
    lib.players = [alice, bob]

    lib.shelves = [Shelf(id=1, name="Living Room", location="Home", capacity=20)]
    lib.venues = [
        Venue(id=1, name="Game Cafe", address="123 Main St", default_for_nights=True)
    ]
    lib.plays = [
        Play(
            id=1,
            game_id=1,
            played_at="2025-06-01T19:30:00",
            duration_minutes=75,
            player_ids=[1, 2],
            winner_ids=[1],
            scores={"1": 10.0, "2": 7.0},
            venue_id=1,
            season_id=None,
        )
    ]
    lib.notes = [
        Note(
            id=1,
            game_id=1,
            body="Great session!",
            created_at="2025-06-01T21:00:00",
        )
    ]
    lib.goals = [
        Goal(
            id=1,
            kind=GoalKind.PLAY_COUNT.value,
            title="Play Catan 5x",
            target=5.0,
            progress=1.0,
            game_id=1,
        )
    ]
    lib.seasons = [
        Season(id=1, name="Summer 2025", start_date="2025-06-01", end_date="2025-08-31")
    ]
    lib.recurring_nights = [
        RecurringNight(
            id=1,
            name="Friday Night",
            weekday="fri",
            usual_player_ids=[1, 2],
            preferred_game_ids=[1],
            active=True,
        )
    ]
    lib.collections = [Collection(id=1, name="Favorites", game_ids=[1], pinned=True)]
    lib.tags = ["family"]
    lib.save()
    return lib


@pytest.fixture
def loaded_library(tmp_path):
    src = FIXTURES / "ludolog-v3.json"
    path = tmp_path / "loaded.json"
    path.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return Library.load(path)


@pytest.fixture
def v0_fixture_data():
    return json.loads((FIXTURES / "ludolog-v0.json").read_text(encoding="utf-8"))


@pytest.fixture
def v1_fixture_data():
    return json.loads((FIXTURES / "ludolog-v1.json").read_text(encoding="utf-8"))


@pytest.fixture
def bgg_csv_path():
    return FIXTURES / "imports" / "bgg_collection.csv"


@pytest.fixture
def bgstats_csv_path():
    return FIXTURES / "imports" / "bgstats_plays.csv"


@pytest.fixture
def ludolog_plays_csv_path():
    return FIXTURES / "imports" / "ludolog_plays.csv"
