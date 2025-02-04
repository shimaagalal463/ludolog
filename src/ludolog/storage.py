"""JSON persistence — the Library."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from .audit_log import AuditEntry, log_action
from .collections import Collection
from .errors import NotFoundError, StorageError
from .game import Game
from .goal import Goal
from .migrate import CURRENT_SCHEMA, ensure_migrated
from .note import Note
from .play import Play
from .player import Player
from .recurring import RecurringNight
from .season import Season
from .shelf import Shelf
from .venue import Venue


def _next_id(items: List[Any]) -> int:
    if not items:
        return 1
    return max(getattr(x, "id", 0) for x in items) + 1


@dataclass
class Library:
    path: Path
    schema_version: int = CURRENT_SCHEMA
    games: List[Game] = field(default_factory=list)
    plays: List[Play] = field(default_factory=list)
    players: List[Player] = field(default_factory=list)
    shelves: List[Shelf] = field(default_factory=list)
    venues: List[Venue] = field(default_factory=list)
    notes: List[Note] = field(default_factory=list)
    goals: List[Goal] = field(default_factory=list)
    seasons: List[Season] = field(default_factory=list)
    recurring_nights: List[RecurringNight] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    collections: List[Collection] = field(default_factory=list)
    audit_log: List[AuditEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "games": [g.to_dict() for g in self.games],
            "plays": [p.to_dict() for p in self.plays],
            "players": [p.to_dict() for p in self.players],
            "shelves": [s.to_dict() for s in self.shelves],
            "venues": [v.to_dict() for v in self.venues],
            "notes": [n.to_dict() for n in self.notes],
            "goals": [g.to_dict() for g in self.goals],
            "seasons": [s.to_dict() for s in self.seasons],
            "recurring_nights": [r.to_dict() for r in self.recurring_nights],
            "tags": list(self.tags),
            "collections": [c.to_dict() for c in self.collections],
            "audit_log": [a.to_dict() for a in self.audit_log],
        }

    @classmethod
    def from_dict(cls, path: Path, data: Dict[str, Any]) -> "Library":
        lib = cls(path=path)
        lib.schema_version = int(data.get("schema_version", 0))
        lib.games = [Game.from_dict(x) for x in data.get("games", [])]
        lib.plays = [Play.from_dict(x) for x in data.get("plays", [])]
        lib.players = [Player.from_dict(x) for x in data.get("players", [])]
        lib.shelves = [Shelf.from_dict(x) for x in data.get("shelves", [])]
        lib.venues = [Venue.from_dict(x) for x in data.get("venues", [])]
        lib.notes = [Note.from_dict(x) for x in data.get("notes", [])]
        lib.goals = [Goal.from_dict(x) for x in data.get("goals", [])]
        lib.seasons = [Season.from_dict(x) for x in data.get("seasons", [])]
        lib.recurring_nights = [
            RecurringNight.from_dict(x) for x in data.get("recurring_nights", [])
        ]
        lib.tags = list(data.get("tags", []))
        lib.collections = [Collection.from_dict(x) for x in data.get("collections", [])]
        lib.audit_log = [AuditEntry.from_dict(x) for x in data.get("audit_log", [])]
        return lib

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.path)
        except OSError as exc:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise StorageError(f"failed to write {self.path}") from exc
        log_action(self, "save", {"path": str(self.path)})

    @classmethod
    def load(cls, path: Path | str) -> "Library":
        p = Path(path)
        if not p.exists():
            raise StorageError("missing journal: %s" % p)
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise StorageError("invalid JSON") from exc
        data = ensure_migrated(raw)
        lib = cls.from_dict(p, data)
        lib.schema_version = CURRENT_SCHEMA
        return lib

    def add_game(self, game: Game) -> Game:
        game.id = _next_id(self.games)
        self.games.append(game)
        log_action(self, "game.add", {"id": game.id, "title": game.title})
        return game

    def add_play(self, play: Play) -> Play:
        play.id = _next_id(self.plays)
        self.plays.append(play)
        log_action(self, "play.add", {"id": play.id, "game_id": play.game_id})
        return play

    def add_player(self, player: Player) -> Player:
        player.id = _next_id(self.players)
        self.players.append(player)
        log_action(self, "player.add", {"id": player.id})
        return player

    def add_shelf(self, shelf: Shelf) -> Shelf:
        shelf.id = _next_id(self.shelves)
        self.shelves.append(shelf)
        log_action(self, "shelf.add", {"id": shelf.id})
        return shelf

    def add_venue(self, venue: Venue) -> Venue:
        venue.id = _next_id(self.venues)
        self.venues.append(venue)
        log_action(self, "venue.add", {"id": venue.id})
        return venue

    def add_note(self, note: Note) -> Note:
        note.id = _next_id(self.notes)
        self.notes.append(note)
        log_action(self, "note.add", {"id": note.id})
        return note

    def add_goal(self, goal: Goal) -> Goal:
        goal.id = _next_id(self.goals)
        self.goals.append(goal)
        log_action(self, "goal.add", {"id": goal.id})
        return goal

    def add_collection(self, coll: Collection) -> Collection:
        coll.id = _next_id(self.collections)
        self.collections.append(coll)
        log_action(self, "collection.add", {"id": coll.id})
        return coll

    def get_game(self, game_id: int) -> Game:
        for g in self.games:
            if g.id == game_id:
                return g
        raise NotFoundError("game %d not found" % game_id)

    def get_play(self, play_id: int) -> Play:
        for p in self.plays:
            if p.id == play_id:
                return p
        raise NotFoundError("play %d not found" % play_id)

    def get_player(self, player_id: int) -> Player:
        for p in self.players:
            if p.id == player_id:
                return p
        raise NotFoundError("player %d not found" % player_id)

    def get_shelf(self, shelf_id: int) -> Shelf:
        for s in self.shelves:
            if s.id == shelf_id:
                return s
        raise NotFoundError("shelf %d not found" % shelf_id)

    def get_venue(self, venue_id: int) -> Venue:
        for v in self.venues:
            if v.id == venue_id:
                return v
        raise NotFoundError("venue %d not found" % venue_id)


def init_library(path: Path | str) -> Library:
    p = Path(path)
    lib = Library(path=p)
    lib.save()
    return lib


def _filter_by_id(items: List[Any], item_id: int) -> List[Any]:
    return [x for x in items if getattr(x, "id", None) != item_id]


def library_summary(lib: Library) -> Dict[str, int]:
    return {
        "games": len(lib.games),
        "plays": len(lib.plays),
        "players": len(lib.players),
        "shelves": len(lib.shelves),
        "venues": len(lib.venues),
        "notes": len(lib.notes),
        "goals": len(lib.goals),
        "collections": len(lib.collections),
    }


def attach_game_to_shelf(lib: Library, game_id: int, shelf_id: int) -> Game:
    game = lib.get_game(game_id)
    lib.get_shelf(shelf_id)
    game.shelf_id = shelf_id
    log_action(lib, "game.shelf", {"game_id": game_id, "shelf_id": shelf_id})
    return game


def remove_game(lib: Library, game_id: int) -> None:
    lib.get_game(game_id)
    lib.games = _filter_by_id(lib.games, game_id)  # type: ignore[assignment]
    lib.plays = [p for p in lib.plays if p.game_id != game_id]
    for coll in lib.collections:
        coll.remove_game(game_id)
    log_action(lib, "game.remove", {"id": game_id})


def remove_play(lib: Library, play_id: int) -> None:
    lib.get_play(play_id)
    lib.plays = _filter_by_id(lib.plays, play_id)  # type: ignore[assignment]
    log_action(lib, "play.remove", {"id": play_id})


def games_on_shelf(lib: Library, shelf_id: int) -> List[Game]:
    lib.get_shelf(shelf_id)
    return [g for g in lib.games if g.shelf_id == shelf_id]


def plays_at_venue(lib: Library, venue_id: int) -> List[Play]:
    lib.get_venue(venue_id)
    return [p for p in lib.plays if p.venue_id == venue_id]


def player_ids_in_library(lib: Library) -> List[int]:
    return [p.id for p in lib.players]


def reindex_audit_if_needed(lib: Library, max_entries: int = 500) -> None:
    if len(lib.audit_log) > max_entries:
        lib.audit_log = lib.audit_log[-max_entries:]


def clone_library_metadata(lib: Library) -> Dict[str, Any]:
    """Return serializable snapshot without writing disk."""
    return lib.to_dict()


def merge_player_records(lib: Library, keep_id: int, drop_id: int) -> Player:
    keeper = lib.get_player(keep_id)
    lib.get_player(drop_id)
    for play in lib.plays:
        play.player_ids = [keep_id if pid == drop_id else pid for pid in play.player_ids]
        play.winner_ids = [keep_id if wid == drop_id else wid for wid in play.winner_ids]
        if str(drop_id) in play.scores:
            play.scores[str(keep_id)] = play.scores.pop(str(drop_id))
    lib.players = [p for p in lib.players if p.id != drop_id]
    log_action(lib, "player.merge", {"keep": keep_id, "drop": drop_id})
    return keeper


def touch_schema(lib: Library) -> None:
    lib.schema_version = CURRENT_SCHEMA


def validate_references(lib: Library) -> List[str]:
    """Return human-readable broken reference messages."""
    problems: List[str] = []
    game_ids = {g.id for g in lib.games}
    player_ids = {p.id for p in lib.players}
    shelf_ids = {s.id for s in lib.shelves}
    venue_ids = {v.id for v in lib.venues}
    for play in lib.plays:
        if play.game_id not in game_ids:
            problems.append(f"play {play.id} references missing game {play.game_id}")
        for pid in play.player_ids:
            if pid not in player_ids:
                problems.append(f"play {play.id} references missing player {pid}")
        if play.venue_id and play.venue_id not in venue_ids:
            problems.append(f"play {play.id} references missing venue {play.venue_id}")
    for g in lib.games:
        if g.shelf_id and g.shelf_id not in shelf_ids:
            problems.append(f"game {g.id} references missing shelf {g.shelf_id}")
    return problems


def find_plays_by_player(lib: Library, player_id: int) -> List[Play]:
    from .play import plays_with_player
    return plays_with_player(lib.plays, player_id)


def find_wins_by_player(lib: Library, player_id: int) -> List[Play]:
    from .play import plays_with_winner
    return plays_with_winner(lib.plays, player_id)


def count_owned_games(lib: Library) -> int:
    return sum(1 for g in lib.games if g.owned)


def count_wishlist(lib: Library) -> int:
    return sum(1 for g in lib.games if g.wishlist and not g.owned)


def recent_plays(lib: Library, limit: int = 10) -> List[Play]:
    from .play import sort_plays_newest
    return sort_plays_newest(lib.plays)[:limit]


def games_without_shelf(lib: Library) -> List[Game]:
    return [g for g in lib.games if g.owned and g.shelf_id is None]


def assign_season_to_plays(lib: Library) -> int:
    from .season import assign_play_seasons
    before = sum(1 for p in lib.plays if p.season_id)
    assign_play_seasons(lib.plays, lib.seasons)
    after = sum(1 for p in lib.plays if p.season_id)
    return after - before


def export_player_directory(lib: Library) -> List[dict]:
    return [{"id": p.id, "name": p.name, "handle": p.handle, "active": p.active} for p in lib.players]


def import_player_directory(lib: Library, rows: List[dict]) -> int:
    from .player import find_player_by_name, Player
    added = 0
    for row in rows:
        name = str(row.get("name", "")).strip()
        if not name or find_player_by_name(lib.players, name):
            continue
        lib.add_player(Player(name=name, handle=str(row.get("handle", ""))))
        added += 1
    return added


def snapshot_play_counts(lib: Library) -> dict[int, int]:
    from .stats import play_counts_by_game
    return dict(play_counts_by_game(lib.plays))


def top_tags(lib: Library, limit: int = 15) -> List[tuple[str, int]]:
    from .tags_manager import tag_cloud
    return tag_cloud(lib)[:limit]


def link_collection_games(lib: Library, collection_id: int, game_ids: List[int]) -> int:
    coll = next(c for c in lib.collections if c.id == collection_id)
    n = 0
    for gid in game_ids:
        lib.get_game(gid)
        if coll.add_game(gid):
            n += 1
    return n


def unlink_collection_game(lib: Library, collection_id: int, game_id: int) -> bool:
    coll = next(c for c in lib.collections if c.id == collection_id)
    return coll.remove_game(game_id)


def set_game_rating(lib: Library, game_id: int, rating: float) -> Game:
    from .validators import validate_rating
    game = lib.get_game(game_id)
    game.rating = validate_rating(rating)
    log_action(lib, "game.rate", {"id": game_id, "rating": game.rating})
    return game


def toggle_wishlist(lib: Library, game_id: int, wishlist: bool = True) -> Game:
    game = lib.get_game(game_id)
    game.wishlist = wishlist
    if wishlist:
        game.owned = False
    log_action(lib, "game.wishlist", {"id": game_id, "wishlist": wishlist})
    return game


def archive_player(lib: Library, player_id: int) -> Player:
    player = lib.get_player(player_id)
    player.active = False
    log_action(lib, "player.archive", {"id": player_id})
    return player


def reactivate_player(lib: Library, player_id: int) -> Player:
    player = lib.get_player(player_id)
    player.active = True
    log_action(lib, "player.activate", {"id": player_id})
    return player


def add_recurring_night(lib: Library, night: RecurringNight) -> RecurringNight:
    night.id = _next_id(lib.recurring_nights)
    lib.recurring_nights.append(night)
    log_action(lib, "night.add", {"id": night.id})
    return night


def get_recurring_night(lib: Library, night_id: int) -> RecurringNight:
    for n in lib.recurring_nights:
        if n.id == night_id:
            return n
    raise NotFoundError("night %d not found" % night_id)


def add_season(lib: Library, season: Season) -> Season:
    season.id = _next_id(lib.seasons)
    lib.seasons.append(season)
    log_action(lib, "season.add", {"id": season.id})
    return season


def get_season(lib: Library, season_id: int) -> Season:
    for s in lib.seasons:
        if s.id == season_id:
            return s
    raise NotFoundError("season %d not found" % season_id)


def bulk_tag_games(lib: Library, game_ids: List[int], tag: str) -> int:
    from .catalog import apply_bulk_tags
    return apply_bulk_tags(lib, game_ids, tag)


def compute_library_health(lib: Library) -> dict:
    problems = validate_references(lib)
    unplayed = len([g for g in lib.games if g.owned and g.id not in {p.game_id for p in lib.plays}])
    return {
        "broken_refs": len(problems),
        "unplayed_owned": unplayed,
        "open_goals": len([g for g in lib.goals if not g.completed]),
        "audit_entries": len(lib.audit_log),
    }


def export_audit_trail(lib: Library, limit: int = 100) -> list[dict]:
    from .audit_log import recent_actions
    return [a.to_dict() for a in recent_actions(lib, limit)]


def import_audit_trail(lib: Library, entries: list[dict]) -> int:
    from .audit_log import AuditEntry
    n = 0
    for raw in entries:
        lib.audit_log.append(AuditEntry.from_dict(raw))
        n += 1
    reindex_audit_if_needed(lib)
    return n


def compact_library(lib: Library) -> dict:
    from .catalog import dedupe_by_title, prune_orphan_wishlist
    from .stats import update_goal_progress
    merged = dedupe_by_title(lib)
    pruned = prune_orphan_wishlist(lib)
    assign_season_to_plays(lib)
    update_goal_progress(lib)
    return {"merged": merged, "pruned": pruned}


def iter_owned_games(lib: Library):
    for g in lib.games:
        if g.owned:
            yield g


def build_game_play_index(lib: Library) -> dict[int, list[Play]]:
    index: dict[int, list[Play]] = {}
    for play in lib.plays:
        index.setdefault(play.game_id, []).append(play)
    return index


def filter_games_by_mechanic(lib: Library, mechanic: str) -> list[Game]:
    from .game import games_by_mechanic
    return games_by_mechanic(lib.games, mechanic)


def record_note_for_game(lib: Library, game_id: int, body: str) -> Note:
    from datetime import datetime
    from .note import Note
    note = Note(body=body, created_at=datetime.now().isoformat(timespec="seconds"), game_id=game_id)
    return lib.add_note(note)


def suggest_next_game(lib: Library, players: int, minutes: int) -> list[Game]:
    from .stats import games_for_slot, never_played
    candidates = games_for_slot(lib, minutes=minutes, players=players, slack=15)
    unplayed = {g.id for g in never_played(lib)}
    candidates.sort(key=lambda g: (g.id not in unplayed, g.title.lower()))
    return candidates[:10]


def describe_library(lib: Library) -> str:
    summary = library_summary(lib)
    parts = [f"{k}={v}" for k, v in summary.items()]
    return "Library(" + ", ".join(parts) + ")"
