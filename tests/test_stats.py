"""Tests for ludolog.stats."""
import pytest

from ludolog.game import Game
from ludolog.goal import Goal, GoalKind
from ludolog.play import Play
from ludolog.player import Player
from ludolog.player_range import PlayerRange
from ludolog.playtime import Playtime
from ludolog.stats import (
    average_duration_by_game,
    average_players_per_session,
    collection_value_estimate,
    compare_player_win_rates,
    compute_stats_dashboard,
    coop_rate,
    game_retention_score,
    games_by_designer,
    games_for_slot,
    h_index_games,
    head_to_head,
    leaderboard,
    mechanic_frequency,
    mechanic_play_counts,
    monthly_unique_games,
    most_played,
    never_played,
    play_counts_by_game,
    player_activity_matrix,
    player_favorite_game,
    player_win_rates,
    plays_by_weekday,
    plays_per_month,
    rating_histogram,
    shelf_fill_rates,
    summary_numbers,
    total_play_minutes,
    update_goal_progress,
    venue_leaderboard,
    win_streak,
)


def test_play_counts_by_game_skips_incomplete(sample_play, sample_play_incomplete):
    counts = play_counts_by_game([sample_play, sample_play_incomplete])
    assert counts[1] == 1


def test_most_played_returns_game_and_count(populated_library):
    results = most_played(populated_library, top=3)
    assert len(results) == 1
    game, count = results[0]
    assert game.title == "Catan"
    assert count == 1


def test_player_win_rates_alice_won(populated_library):
    rates = player_win_rates(populated_library)
    alice = next(r for r in rates if r[0] == "alice")
    assert alice[1] == 1.0
    assert alice[2] == 1


def test_games_for_slot_filters_owned_and_fit(populated_library):
    games = games_for_slot(populated_library, minutes=75, players=4)
    titles = [g.title for g in games]
    assert "Catan" in titles
    assert "Ark Nova" not in titles


def test_mechanic_frequency_counts_games(populated_library):
    freq = mechanic_frequency(populated_library)
    labels = [m for m, _ in freq]
    assert "cooperative" in labels


def test_never_played_owned_without_plays(populated_library):
    unplayed = never_played(populated_library)
    titles = [g.title for g in unplayed]
    assert "Pandemic" in titles
    assert "Catan" not in titles


def test_average_duration_by_game(sample_play):
    avg = average_duration_by_game([sample_play])
    assert avg[1] == 75.0


def test_update_goal_progress_play_count(populated_library):
    update_goal_progress(populated_library)
    goal = populated_library.goals[0]
    assert goal.progress == 1.0


def test_update_goal_progress_win_rate(tmp_journal):
    p = tmp_journal.add_player(Player(name="Pat"))
    tmp_journal.add_game(Game(title="G"))
    tmp_journal.add_play(Play(game_id=1, played_at="2025-01-01", player_ids=[1], winner_ids=[1]))
    tmp_journal.add_goal(Goal(kind=GoalKind.WIN_RATE.value, player_id=1, target=50.0))
    update_goal_progress(tmp_journal)
    assert tmp_journal.goals[0].progress == 100.0


def test_plays_per_month_groups_by_month(populated_library):
    months = plays_per_month(populated_library)
    assert months == [("2025-06", 1)]


def test_average_players_per_session(populated_library):
    assert average_players_per_session(populated_library) == 2.0


def test_total_play_minutes(populated_library):
    assert total_play_minutes(populated_library) == 75


def test_games_by_designer(populated_library):
    designers = games_by_designer(populated_library)
    names = [d for d, _ in designers]
    assert "Klaus Teuber" in names


def test_h_index_games():
    plays = [Play(game_id=1), Play(game_id=1), Play(game_id=2)]
    assert h_index_games(plays) == 1


def test_player_favorite_game(populated_library):
    game, count = player_favorite_game(populated_library, 1)
    assert game.title == "Catan"
    assert count == 1


def test_win_streak_current(populated_library):
    assert win_streak(populated_library, 1) == 1
    assert win_streak(populated_library, 2) == 0


def test_mechanic_play_counts_from_plays(populated_library):
    counts = mechanic_play_counts(populated_library)
    assert counts[0][0] in ("trading", "dice rolling")


def test_collection_value_estimate(populated_library):
    value = collection_value_estimate(populated_library, default_price=40.0)
    assert value > 80.0


def test_compare_player_win_rates(populated_library):
    ra, rb = compare_player_win_rates(populated_library, 1, 2)
    assert ra == 1.0
    assert rb == 0.0


def test_head_to_head_single_session(populated_library):
    aw, bw, ties = head_to_head(populated_library, 1, 2)
    assert aw == 1
    assert bw == 0
    assert ties == 0


def test_leaderboard_orders_by_wins(populated_library):
    board = leaderboard(populated_library)
    assert board[0][0] == "alice"
    assert board[0][1] == 1


def test_monthly_unique_games(populated_library):
    rows = monthly_unique_games(populated_library)
    assert rows == [("2025-06", 1)]


def test_player_activity_matrix(populated_library):
    matrix = player_activity_matrix(populated_library)
    assert matrix[1][1] == 1
    assert matrix[1][2] == 1


def test_venue_leaderboard(populated_library):
    board = venue_leaderboard(populated_library)
    assert board[0][0] == "Game Cafe"
    assert board[0][1] == 1


def test_shelf_fill_rates(populated_library):
    rates = shelf_fill_rates(populated_library)
    assert rates[0][0] == "Living Room"
    assert rates[0][1] == 0.05


def test_rating_histogram(populated_library):
    hist = rating_histogram(populated_library)
    buckets = dict(hist)
    assert buckets[8] == 1
    assert buckets[9] == 1


def test_summary_numbers(populated_library):
    nums = summary_numbers(populated_library)
    assert nums["games"] == 3
    assert nums["plays"] == 1
    assert nums["players"] == 2
    assert nums["avg_players"] == 2.0
    assert nums["minutes"] == 75


def test_plays_by_weekday_has_seven_days(populated_library):
    rows = plays_by_weekday(populated_library)
    assert len(rows) == 7
    assert sum(c for _, c in rows) == 1


def test_coop_rate_zero_without_coop_sessions(populated_library):
    assert coop_rate(populated_library) == 0.0


def test_compute_stats_dashboard_keys(populated_library):
    dash = compute_stats_dashboard(populated_library)
    assert "summary" in dash
    assert dash["h_index"] == 1
    assert dash["backlog_nights"] == pytest.approx(0.6666666666666666)


def test_game_retention_score_single_play_returns_zero(populated_library):
    assert game_retention_score(populated_library, 1) == 0.0
