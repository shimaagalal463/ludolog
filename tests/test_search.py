"""Tests for ludolog.search."""
from ludolog.game import Game
from ludolog.player import Player
from ludolog.player_range import PlayerRange
from ludolog.playtime import Playtime
from ludolog.search import (
    autocomplete_titles,
    filter_games,
    games_by_mechanic,
    ranked_wishlist,
    search_all,
    search_by_designer,
    search_by_tag,
    search_games,
    search_notes,
    search_players,
    similar_games,
    suggest_for_player,
)


def test_search_games_exact_title_match(populated_library):
    hits = search_games(populated_library, "Catan")
    assert len(hits) == 1
    assert hits[0].kind == "game"
    assert hits[0].ref_id == 1
    assert hits[0].score == 100.0


def test_search_games_prefix_scores_higher_than_substring(populated_library):
    hits = search_games(populated_library, "Pan")
    titles = [h.label for h in hits]
    assert "Pandemic" in titles
    assert hits[0].label == "Pandemic"
    assert hits[0].score == 80.0


def test_search_games_matches_designer(populated_library):
    hits = search_games(populated_library, "Teuber")
    assert any(h.label == "Catan" for h in hits)


def test_search_games_matches_tag(populated_library):
    hits = search_games(populated_library, "classic")
    assert any(h.label == "Catan" for h in hits)


def test_search_games_empty_query_returns_nothing(populated_library):
    assert search_games(populated_library, "") == []


def test_search_games_respects_limit(populated_library):
    hits = search_games(populated_library, "a", limit=1)
    assert len(hits) == 1


def test_search_players_by_name(populated_library):
    hits = search_players(populated_library, "Alice")
    assert len(hits) == 1
    assert hits[0].kind == "player"
    assert hits[0].label == "alice"


def test_search_players_by_handle(populated_library):
    hits = search_players(populated_library, "bob")
    assert len(hits) == 1
    assert hits[0].ref_id == 2


def test_search_all_merges_games_and_players(populated_library):
    hits = search_all(populated_library, "cat", limit=10)
    kinds = {h.kind for h in hits}
    assert "game" in kinds


def test_games_by_mechanic_returns_ids(populated_library):
    ids = games_by_mechanic(populated_library, "cooperative")
    assert 2 in ids
    assert 1 not in ids


def test_similar_games_mechanic_overlap(populated_library):
    hits = similar_games(populated_library, 1, limit=5)
    assert all(h.kind == "game" for h in hits)
    assert all(h.ref_id != 1 for h in hits)


def test_search_by_designer(populated_library):
    hits = search_by_designer(populated_library, "Leacock")
    assert len(hits) == 1
    assert hits[0].label == "Pandemic"


def test_search_by_tag_case_insensitive(populated_library):
    hits = search_by_tag(populated_library, "CLASSIC")
    assert len(hits) == 1
    assert hits[0].label == "Catan"
    assert hits[0].score == 100.0


def test_filter_games_owned_only(populated_library):
    hits = filter_games(populated_library, owned=True)
    titles = {h.label for h in hits}
    assert "Catan" in titles
    assert "Ark Nova" not in titles


def test_filter_games_wishlist_only(populated_library):
    hits = filter_games(populated_library, wishlist=True)
    assert len(hits) == 1
    assert hits[0].label == "Ark Nova"


def test_filter_games_min_players(populated_library):
    hits = filter_games(populated_library, min_players=4)
    titles = {h.label for h in hits}
    assert "Catan" in titles
    for hit in hits:
        game = populated_library.get_game(hit.ref_id)
        assert game.fits_players(4)


def test_filter_games_max_minutes(populated_library):
    hits = filter_games(populated_library, max_minutes=60)
    titles = {h.label for h in hits}
    assert "Pandemic" in titles
    assert "Ark Nova" not in titles


def test_suggest_for_player_no_favorites_returns_empty(populated_library):
    assert suggest_for_player(populated_library, 1) == []


def test_suggest_for_player_matches_favorite_mechanics(tmp_journal):
    player = tmp_journal.add_player(Player(name="Fan", favorite_mechanics=["cooperative"]))
    tmp_journal.add_game(Game(title="Coop Game", owned=True, mechanics=["cooperative"]))
    tmp_journal.add_game(Game(title="Solo Auction", owned=True, mechanics=["auction"]))
    hits = suggest_for_player(tmp_journal, player.id)
    assert len(hits) == 1
    assert hits[0].label == "Coop Game"


def test_autocomplete_titles_prefix(populated_library):
    titles = autocomplete_titles(populated_library, "cat")
    assert titles == ["Catan"]


def test_search_notes_finds_body(populated_library):
    hits = search_notes(populated_library, "session")
    assert len(hits) == 1
    assert hits[0].kind == "note"
    assert "Great session" in hits[0].label


def test_ranked_wishlist_orders_by_rating(populated_library):
    hits = ranked_wishlist(populated_library)
    assert len(hits) == 1
    assert hits[0].label == "Ark Nova"
    assert hits[0].score == 9.0

