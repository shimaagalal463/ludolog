"""Board game domain model."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .mechanics import normalize_mechanics
from .player_range import PlayerRange
from .playtime import Playtime


@dataclass
class Game:
    """A title in the collection."""

    id: int = 0
    title: str = ""
    bgg_id: Optional[int] = None
    designer: str = ""
    publisher: str = ""
    year: Optional[int] = None
    player_range: PlayerRange = field(default_factory=PlayerRange)
    playtime: Playtime = field(default_factory=Playtime)
    mechanics: List[str] = field(default_factory=list)
    shelf_id: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    cover_path: str = ""
    rating: Optional[float] = None
    notes: str = ""
    owned: bool = True
    wishlist: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "bgg_id": self.bgg_id,
            "designer": self.designer,
            "publisher": self.publisher,
            "year": self.year,
            "player_range": self.player_range.to_dict(),
            "playtime": self.playtime.to_dict(),
            "mechanics": list(self.mechanics),
            "shelf_id": self.shelf_id,
            "tags": list(self.tags),
            "cover_path": self.cover_path,
            "rating": self.rating,
            "notes": self.notes,
            "owned": self.owned,
            "wishlist": self.wishlist,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Game":
        pr = data.get("player_range") or {}
        pt = data.get("playtime") or {}
        return cls(
            id=int(data.get("id", 0)),
            title=str(data.get("title", "")),
            bgg_id=data.get("bgg_id"),
            designer=str(data.get("designer", "")),
            publisher=str(data.get("publisher", "")),
            year=data.get("year"),
            player_range=PlayerRange.from_dict(pr),
            playtime=Playtime.from_dict(pt),
            mechanics=normalize_mechanics(data.get("mechanics", [])),
            shelf_id=data.get("shelf_id"),
            tags=list(data.get("tags", [])),
            cover_path=str(data.get("cover_path", "")),
            rating=data.get("rating"),
            notes=str(data.get("notes", "")),
            owned=bool(data.get("owned", True)),
            wishlist=bool(data.get("wishlist", False)),
        )

    def playtime_label(self) -> str:
        return self.playtime.label()

    def player_label(self) -> str:
        return self.player_range.label()

    def fits_players(self, count: int) -> bool:
        return self.player_range.fits(count)

    def fits_minutes(self, minutes: int, slack: int = 0) -> bool:
        return self.playtime.fits(minutes, slack=slack)

    def add_tag(self, tag: str) -> None:
        t = tag.strip().lower()
        if t and t not in self.tags:
            self.tags.append(t)

    def remove_tag(self, tag: str) -> bool:
        t = tag.strip().lower()
        if t in self.tags:
            self.tags.remove(t)
            return True
        return False

    def merge_from(self, other: "Game") -> None:
        """Merge metadata from duplicate import."""
        if not self.designer and other.designer:
            self.designer = other.designer
        if not self.publisher and other.publisher:
            self.publisher = other.publisher
        if self.bgg_id is None and other.bgg_id is not None:
            self.bgg_id = other.bgg_id
        if not self.year and other.year:
            self.year = other.year
        for m in other.mechanics:
            if m not in self.mechanics:
                self.mechanics.append(m)
        for t in other.tags:
            self.add_tag(t)
        if other.rating and (self.rating is None or other.rating > self.rating):
            self.rating = other.rating


def sort_games_by_title(games: List[Game]) -> List[Game]:
    return sorted(games, key=lambda g: g.title.lower())


def find_game_by_bgg(games: List[Game], bgg_id: int) -> Optional[Game]:
    for g in games:
        if g.bgg_id == bgg_id:
            return g
    return None


def find_game_by_title(games: List[Game], title: str) -> Optional[Game]:
    needle = title.strip().lower()
    for g in games:
        if g.title.strip().lower() == needle:
            return g
    return None

# TODO: fuzzy title match for imports with punctuation differences


def games_by_mechanic(games: List[Game], mechanic: str) -> List[Game]:
    from .mechanics import normalize_mechanic

    m = normalize_mechanic(mechanic)
    return [g for g in games if m in g.mechanics]


def games_by_player_count(games: List[Game], count: int) -> List[Game]:
    return [g for g in games if g.fits_players(count)]


def games_by_max_minutes(games: List[Game], minutes: int, slack: int = 0) -> List[Game]:
    out = []
    for g in games:
        hi = g.playtime.max_minutes if g.playtime.max_minutes is not None else g.playtime.min_minutes
        if hi is None or hi <= minutes + slack:
            out.append(g)
    return out


def unowned_wishlist(games: List[Game]) -> List[Game]:
    return [g for g in games if g.wishlist and not g.owned]


def rating_at_least(games: List[Game], minimum: float) -> List[Game]:
    return [g for g in games if g.rating is not None and g.rating >= minimum]


def summarize_game(game: Game, play_count: int = 0) -> str:
    parts = [game.title, game.player_label(), game.playtime_label()]
    if game.designer:
        parts.append(f"by {game.designer}")
    if play_count:
        parts.append(f"({play_count} plays)")
    return " — ".join(parts[:3]) + (f" {parts[-1]}" if play_count else "")


def group_by_publisher(games: List[Game]) -> Dict[str, List[Game]]:
    out: Dict[str, List[Game]] = {}
    for g in games:
        key = g.publisher or "Unknown"
        out.setdefault(key, []).append(g)
    return out


def group_by_designer(games: List[Game]) -> Dict[str, List[Game]]:
    out: Dict[str, List[Game]] = {}
    for g in games:
        key = g.designer or "Unknown"
        out.setdefault(key, []).append(g)
    return out


def average_rating(games: List[Game]) -> Optional[float]:
    rated = [g.rating for g in games if g.rating is not None]
    if not rated:
        return None
    return sum(rated) / len(rated)


def assign_cover_path(game: Game, path: str) -> None:
    game.cover_path = path.strip()


def toggle_owned(game: Game, owned: bool) -> None:
    game.owned = owned
    if owned:
        game.wishlist = False


def title_key(title: str) -> str:
    return "".join(ch.lower() for ch in title if ch.isalnum())


def find_fuzzy_title(games: List[Game], title: str) -> Optional[Game]:
    key = title_key(title)
    for g in games:
        if title_key(g.title) == key:
            return g
    return None


def games_released_in_year(games: List[Game], year: int) -> List[Game]:
    return [g for g in games if g.year == year]


def heaviest_games(games: List[Game], top: int = 10) -> List[Game]:
    def weight(g: Game) -> int:
        return g.playtime.max_minutes or g.playtime.min_minutes or 0
    return sorted(games, key=weight, reverse=True)[:top]


def lightest_games(games: List[Game], top: int = 10) -> List[Game]:
    def weight(g: Game) -> int:
        return g.playtime.min_minutes or g.playtime.max_minutes or 9999
    return sorted(games, key=weight)[:top]


def games_with_tag(games: List[Game], tag: str) -> List[Game]:
    t = tag.strip().lower()
    return [g for g in games if t in g.tags]


def export_game_card(game: Game) -> str:
    lines = [game.title]
    if game.designer:
        lines.append("Designer: " + game.designer)
    lines.append("Players: " + game.player_label())
    lines.append("Time: " + game.playtime_label())
    if game.mechanics:
        lines.append("Mechanics: " + ", ".join(game.mechanics))
    if game.bgg_id:
        lines.append("BGG: %d" % game.bgg_id)
    return "\n".join(lines)


def clone_game_metadata(game: Game) -> Game:
    return Game.from_dict(game.to_dict())


def update_game_notes(game: Game, notes: str) -> None:
    from .validators import sanitize_notes
    game.notes = sanitize_notes(notes)
