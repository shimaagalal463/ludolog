"""Tests for ludolog.scoreboard."""
from __future__ import annotations

from ludolog.play import Play
from ludolog.player import Player
from ludolog.scoreboard import (
    aggregate_wins,
    build_standings,
    coop_sessions,
    export_standings_text,
    format_leaderboard,
    lowest_scorers,
    per_player_average,
    player_participation,
    rank_by_scores,
    score_spread,
    scoreboard_lines,
    win_rate,
    winner_names,
)


def test_rank_by_scores_descending(sample_play):
    ranked = rank_by_scores(sample_play)
    assert ranked[0] == (1, 10.0)
    assert ranked[1] == (2, 7.0)


def test_rank_by_scores_tiebreaker_by_id():
    play = Play(scores={"3": 5.0, "1": 5.0})
    ranked = rank_by_scores(play)
    assert ranked[0][0] == 1
    assert ranked[1][0] == 3


def test_winner_names(sample_play, sample_player, sample_player2):
    names = winner_names(sample_play, [sample_player, sample_player2])
    assert names == ["alice"]


def test_winner_names_missing_player_fallback():
    play = Play(winner_ids=[99])
    assert winner_names(play, []) == ["#99"]


def test_scoreboard_lines_marks_winners(sample_play, sample_player, sample_player2):
    lines = scoreboard_lines(sample_play, [sample_player, sample_player2])
    assert lines[0].startswith("*")
    assert "alice: 10" in lines[0]
    assert lines[1].startswith(" ")


def test_aggregate_wins(sample_play, sample_player2):
    play2 = Play(
        game_id=1,
        player_ids=[2],
        winner_ids=[2],
        incomplete=False,
    )
    wins = aggregate_wins([sample_play, play2])
    assert wins[1] == 1
    assert wins[2] == 1


def test_aggregate_wins_skips_incomplete(sample_play_incomplete):
    wins = aggregate_wins([sample_play_incomplete])
    assert wins == {}


def test_win_rate():
    assert win_rate(3, 6) == 0.5


def test_win_rate_zero_games():
    assert win_rate(0, 0) is None


def test_player_participation(sample_play, sample_player):
    assert player_participation([sample_play], sample_player.id) == 1
    assert player_participation([sample_play], 99) == 0


def test_coop_sessions():
    coop = Play(player_ids=[1, 2], winner_ids=[1, 2])
    solo = Play(player_ids=[1, 2], winner_ids=[1])
    result = coop_sessions([coop, solo])
    assert result == [coop]


def test_lowest_scorers():
    play = Play(scores={"1": 10.0, "2": 3.0, "3": 3.0})
    assert sorted(lowest_scorers(play)) == [2, 3]


def test_lowest_scorers_empty():
    assert lowest_scorers(Play()) == []


def test_score_spread():
    play = Play(scores={"1": 10.0, "2": 4.0})
    assert score_spread(play) == 6.0


def test_score_spread_single_score():
    assert score_spread(Play(scores={"1": 5.0})) is None


def test_per_player_average():
    plays = [
        Play(scores={"1": 10.0}),
        Play(scores={"1": 6.0}),
    ]
    assert per_player_average(plays, 1) == 8.0


def test_per_player_average_no_scores():
    assert per_player_average([Play(player_ids=[1])], 1) is None


def test_format_leaderboard():
    rows = [("Alice", 0.667, 3), ("Bob", 0.333, 3)]
    text = format_leaderboard(rows)
    assert "Alice: 66.7%" in text
    assert "3 games" in text


def test_build_standings(sample_play, sample_player, sample_player2):
    rows = build_standings([sample_play], [sample_player, sample_player2])
    assert rows[0][0] == "alice"
    assert rows[0][1] == 1
    assert rows[0][2] == 1


def test_build_standings_filters_by_game(sample_play, sample_player, sample_player2):
    other = Play(game_id=99, player_ids=[1, 2], winner_ids=[2])
    rows = build_standings([sample_play, other], [sample_player, sample_player2], game_id=1)
    assert len(rows) == 2
    assert all(r[2] == 1 for r in rows)


def test_build_standings_excludes_non_participants():
    p1 = Player(id=1, name="Alice", handle="alice")
    p2 = Player(id=2, name="Bob", handle="bob")
    play = Play(player_ids=[1], winner_ids=[1])
    rows = build_standings([play], [p1, p2])
    assert len(rows) == 1
    assert rows[0][0] == "alice"


def test_export_standings_text(sample_play, sample_player, sample_player2):
    text = export_standings_text([sample_play], [sample_player, sample_player2])
    assert "alice" in text
    assert "100.0%" in text
