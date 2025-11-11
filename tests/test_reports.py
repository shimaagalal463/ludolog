"""Tests for ludolog.reports."""
import pytest

from ludolog.errors import NotFoundError
from ludolog.play import Play
from ludolog.reports import (
    backlog_report,
    collection_report,
    compare_players_report,
    format_play_line,
    full_report,
    game_night_report,
    goals_report,
    mechanic_report,
    player_report,
    recurring_report,
    season_report,
    shelf_report,
    summary_report,
    venue_report,
)


def test_summary_report_counts(populated_library):
    text = summary_report(populated_library)
    assert "ludolog summary" in text
    assert "games: 3 (owned 2)" in text
    assert "plays: 1" in text
    assert "players: 2" in text
    assert "most played:" in text
    assert "Catan — 1" in text


def test_summary_report_lists_never_played(populated_library):
    text = summary_report(populated_library)
    assert "never played" in text
    assert "Pandemic" in text


def test_game_night_report_includes_recent_play(populated_library):
    text = game_night_report(populated_library, days=5000)
    assert "game night report" in text
    assert "sessions: 1" in text
    assert "Catan" in text
    assert "winners: alice" in text


def test_game_night_report_empty_window(tmp_journal):
    text = game_night_report(tmp_journal, days=7)
    assert "sessions: 0" in text


def test_player_report_shows_win_rate(populated_library):
    text = player_report(populated_library, 1)
    assert "player: alice" in text
    assert "win rate:" in text
    assert "recent plays:" in text


def test_player_report_missing_raises(populated_library):
    with pytest.raises(NotFoundError, match="player 99"):
        player_report(populated_library, 99)


def test_shelf_report_lists_games_on_shelf(populated_library):
    text = shelf_report(populated_library, 1)
    assert "shelf:" in text
    assert "Living Room" in text
    assert "games: 1" in text
    assert "capacity: 20 (1/20)" in text
    assert "Catan" in text


def test_season_report_counts_plays_in_range(populated_library):
    text = season_report(populated_library, 1)
    assert "season: Summer 2025" in text
    assert "plays: 1" in text
    assert "Catan: 1" in text


def test_season_report_missing_raises(populated_library):
    with pytest.raises(NotFoundError, match="season 99"):
        season_report(populated_library, 99)


def test_mechanic_report_owned_and_plays(populated_library):
    text = mechanic_report(populated_library, "cooperative")
    assert "mechanic: cooperative" in text
    assert "owned: 1" in text
    assert "plays logged: 0" in text
    assert "Pandemic" in text


def test_venue_report_lists_sessions(populated_library):
    text = venue_report(populated_library, 1)
    assert "venue: Game Cafe" in text
    assert "sessions: 1" in text
    assert "Catan" in text


def test_format_play_line(populated_library):
    play = populated_library.plays[0]
    line = format_play_line(play, "Catan")
    assert "Catan" in line
    assert "2p" in line
    assert play.played_date() in line


def test_collection_report_lists_member_games(populated_library):
    text = collection_report(populated_library, 1)
    assert "collection: Favorites" in text
    assert "Catan" in text


def test_collection_report_missing_raises(populated_library):
    with pytest.raises(NotFoundError, match="collection 99"):
        collection_report(populated_library, 99)


def test_goals_report_shows_open_goal(populated_library):
    text = goals_report(populated_library)
    assert "open goals:" in text
    assert "Play Catan 5x" in text
    assert "20%" in text


def test_goals_report_none_when_empty(tmp_journal):
    text = goals_report(tmp_journal)
    assert "(none)" in text


def test_recurring_report_lists_active_nights(populated_library):
    text = recurring_report(populated_library)
    assert "recurring game nights:" in text
    assert "Friday Night" in text
    assert "Fri" in text or "fri" in text.lower()


def test_full_report_joins_sections(populated_library):
    text = full_report(populated_library)
    assert "ludolog summary" in text
    assert "open goals:" in text
    assert "recurring game nights:" in text


def test_compare_players_report_head_to_head(populated_library):
    text = compare_players_report(populated_library, 1, 2)
    assert "alice vs bob" in text
    assert "win rates:" in text
    assert "head-to-head:" in text


def test_backlog_report_lists_unplayed_owned(populated_library):
    text = backlog_report(populated_library)
    assert "unplayed owned: 1" in text
    assert "Pandemic" in text
