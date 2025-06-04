"""Tests for ludolog.game."""
from ludolog.game import (
    Game,
    assign_cover_path,
    average_rating,
    clone_game_metadata,
    export_game_card,
    find_fuzzy_title,
    find_game_by_bgg,
    find_game_by_title,
    games_by_max_minutes,
    games_by_mechanic,
    games_by_player_count,
    games_released_in_year,
    games_with_tag,
    group_by_designer,
    group_by_publisher,
    heaviest_games,
    lightest_games,
    rating_at_least,
    sort_games_by_title,
    summarize_game,
    title_key,
    toggle_owned,
    unowned_wishlist,
    update_game_notes,
)
from ludolog.player_range import PlayerRange
from ludolog.playtime import Playtime


def test_game_to_dict_roundtrip(sample_game):
    restored = Game.from_dict(sample_game.to_dict())
    assert restored.title == "Catan"
    assert restored.bgg_id == 13
    assert restored.mechanics == sample_game.mechanics


def test_fits_players(sample_game):
    assert sample_game.fits_players(4) is True
    assert sample_game.fits_players(2) is False


def test_fits_minutes_with_slack(sample_game):
    assert sample_game.fits_minutes(60) is True
    assert sample_game.fits_minutes(95, slack=10) is True
    assert sample_game.fits_minutes(120) is False


def test_add_tag_normalizes_and_dedupes(sample_game):
    sample_game.add_tag("  EURO  ")
    sample_game.add_tag("euro")
    assert sample_game.tags.count("euro") == 1
    assert "classic" in sample_game.tags


def test_remove_tag(sample_game):
    assert sample_game.remove_tag("classic") is True
    assert "classic" not in sample_game.tags
    assert sample_game.remove_tag("missing") is False


def test_merge_from_fills_gaps_and_higher_rating():
    base = Game(id=1, title="Root", mechanics=["area control"])
    donor = Game(
        designer="Cole Wehrle",
        publisher="Leder",
        bgg_id=237182,
        year=2018,
        mechanics=["negotiation"],
        tags=["asymmetric"],
        rating=8.8,
    )
    base.merge_from(donor)
    assert base.designer == "Cole Wehrle"
    assert base.publisher == "Leder"
    assert base.bgg_id == 237182
    assert "negotiation" in base.mechanics
    assert "asymmetric" in base.tags
    assert base.rating == 8.8


def test_sort_games_by_title_case_insensitive(sample_game, sample_game2, sample_game_wishlist):
    games = [sample_game2, sample_game_wishlist, sample_game]
    sorted_games = sort_games_by_title(games)
    assert [g.title for g in sorted_games] == ["Ark Nova", "Catan", "Pandemic"]


def test_find_game_by_bgg(sample_game, sample_game2):
    games = [sample_game, sample_game2]
    assert find_game_by_bgg(games, 13) is sample_game
    assert find_game_by_bgg(games, 99999) is None


def test_find_game_by_title_strips_and_lowercases(sample_game):
    games = [sample_game]
    assert find_game_by_title(games, "  catan ") is sample_game
    assert find_game_by_title(games, "Monopoly") is None


def test_games_by_mechanic_normalizes(sample_game, sample_game2):
    games = [sample_game, sample_game2]
    trading = games_by_mechanic(games, "Dice-Rolling")
    assert len(trading) == 1
    assert trading[0].title == "Catan"
    coop = games_by_mechanic(games, "Cooperative")
    assert len(coop) == 1
    assert coop[0].title == "Pandemic"


def test_games_by_player_count(sample_game, sample_game2, sample_game_wishlist):
    games = [sample_game, sample_game2, sample_game_wishlist]
    four_player = games_by_player_count(games, 4)
    assert {g.title for g in four_player} == {"Catan", "Pandemic", "Ark Nova"}
    assert games_by_player_count(games, 5) == []


def test_games_by_max_minutes(sample_game, sample_game2):
    games = [sample_game, sample_game2]
    short = games_by_max_minutes(games, 50)
    assert len(short) == 1
    assert short[0].title == "Pandemic"


def test_unowned_wishlist(sample_game, sample_game_wishlist):
    games = [sample_game, sample_game_wishlist]
    wishlist = unowned_wishlist(games)
    assert len(wishlist) == 1
    assert wishlist[0].title == "Ark Nova"


def test_rating_at_least(sample_game, sample_game2, sample_game_wishlist):
    games = [sample_game, sample_game2, sample_game_wishlist]
    rated = rating_at_least(games, 9.0)
    assert len(rated) == 1
    assert rated[0].title == "Ark Nova"


def test_summarize_game_with_play_count(sample_game):
    text = summarize_game(sample_game, play_count=12)
    assert text.startswith("Catan — ")
    assert text.endswith("(12 plays)")


def test_group_by_publisher_uses_unknown(sample_game, sample_game2):
    groups = group_by_publisher([sample_game, sample_game2])
    assert "Kosmos" in groups
    assert "Unknown" in groups
    assert groups["Unknown"][0].title == "Pandemic"


def test_group_by_designer(sample_game, sample_game2):
    groups = group_by_designer([sample_game, sample_game2])
    assert groups["Klaus Teuber"][0].title == "Catan"
    assert groups["Matt Leacock"][0].title == "Pandemic"


def test_average_rating_empty_and_populated(sample_game, sample_game2, sample_game_wishlist):
    assert average_rating([sample_game2]) is None
    avg = average_rating([sample_game, sample_game_wishlist])
    assert round(avg, 2) == 8.75


def test_assign_cover_path_strips(sample_game):
    assign_cover_path(sample_game, "  covers/catan.jpg  ")
    assert sample_game.cover_path == "covers/catan.jpg"


def test_toggle_owned_clears_wishlist(sample_game_wishlist):
    toggle_owned(sample_game_wishlist, True)
    assert sample_game_wishlist.owned is True
    assert sample_game_wishlist.wishlist is False


def test_title_key_and_find_fuzzy_title(sample_game):
    assert title_key("Catan: Seafarers!") == "catanseafarers"
    games = [sample_game]
    assert find_fuzzy_title(games, "Catan!") is sample_game


def test_games_released_in_year(sample_game, sample_game2):
    games = [sample_game, sample_game2]
    assert len(games_released_in_year(games, 1995)) == 1
    assert games_released_in_year(games, 1995)[0].title == "Catan"


def test_heaviest_and_lightest_games(sample_game, sample_game2, sample_game_wishlist):
    games = [sample_game, sample_game2, sample_game_wishlist]
    assert heaviest_games(games, top=1)[0].title == "Ark Nova"
    assert lightest_games(games, top=1)[0].title == "Pandemic"


def test_games_with_tag(sample_game):
    assert games_with_tag([sample_game], "CLASSIC")[0].title == "Catan"
    assert games_with_tag([sample_game], "deckbuilding") == []


def test_export_game_card(sample_game):
    card = export_game_card(sample_game)
    assert "Catan" in card
    assert "Designer: Klaus Teuber" in card
    assert "BGG: 13" in card
    assert "Mechanics:" in card


def test_clone_game_metadata_is_independent_copy(sample_game):
    clone = clone_game_metadata(sample_game)
    clone.title = "Modified"
    assert sample_game.title == "Catan"
    assert clone.rating == sample_game.rating


def test_update_game_notes_sanitizes(sample_game):
    update_game_notes(sample_game, "  trimmed note  ")
    assert sample_game.notes == "trimmed note"
