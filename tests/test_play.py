"""Tests for ludolog.play."""
from datetime import date

from ludolog.play import (
    Play,
    average_duration,
    clear_winners,
    copy_play_template,
    days_since_last_play,
    duration_label,
    first_play,
    format_play_summary,
    last_play,
    mark_all_winners,
    merge_scores,
    multi_game_sessions,
    plays_for_game,
    plays_in_range,
    plays_on_date,
    plays_with_player,
    plays_with_winner,
    sort_plays_newest,
    total_duration,
    validate_play_roster,
)


def test_played_datetime_iso():
    p = Play(played_at="2025-06-01T19:30:00")
    assert p.played_datetime().year == 2025


def test_played_datetime_date_only():
    p = Play(played_at="2025-06-01")
    assert p.played_date() == "2025-06-01"


def test_played_datetime_empty_uses_now():
    p = Play(played_at="")
    assert p.played_datetime().year >= 2020


def test_player_count():
    p = Play(player_ids=[1, 2, 3])
    assert p.player_count() == 3


def test_has_winner_true():
    assert Play(winner_ids=[1]).has_winner() is True


def test_has_winner_false():
    assert Play(winner_ids=[]).has_winner() is False


def test_is_coop_win_all_players():
    p = Play(player_ids=[1, 2], winner_ids=[1, 2])
    assert p.is_coop_win() is True


def test_is_coop_win_partial():
    p = Play(player_ids=[1, 2], winner_ids=[1])
    assert p.is_coop_win() is False


def test_set_and_get_score():
    p = Play()
    p.set_score(1, 10.5)
    assert p.get_score(1) == 10.5


def test_highest_scorers():
    p = Play(scores={"1": 10.0, "2": 10.0, "3": 5.0})
    assert set(p.highest_scorers()) == {1, 2}


def test_infer_winners_from_scores():
    p = Play(player_ids=[1, 2], scores={"1": 15.0, "2": 10.0})
    p.infer_winners_from_scores()
    assert p.winner_ids == [1]


def test_to_dict_roundtrip():
    p = Play(id=1, game_id=2, played_at="2025-01-01", scores={"1": 5.0}, incomplete=True)
    restored = Play.from_dict(p.to_dict())
    assert restored.incomplete is True
    assert restored.scores["1"] == 5.0


def test_plays_for_game():
    plays = [Play(game_id=1), Play(game_id=2), Play(game_id=1)]
    assert len(plays_for_game(plays, 1)) == 2


def test_plays_in_range():
    plays = [
        Play(played_at="2025-06-01"),
        Play(played_at="2025-06-15"),
        Play(played_at="2025-07-01"),
    ]
    result = plays_in_range(plays, "2025-06-01", "2025-06-30")
    assert len(result) == 2


def test_sort_plays_newest():
    plays = [Play(played_at="2025-01-01"), Play(played_at="2025-06-01")]
    sorted_p = sort_plays_newest(plays)
    assert sorted_p[0].played_at == "2025-06-01"


def test_plays_with_player():
    plays = [Play(player_ids=[1, 2]), Play(player_ids=[3])]
    assert len(plays_with_player(plays, 1)) == 1


def test_plays_with_winner():
    plays = [Play(winner_ids=[1]), Play(winner_ids=[2])]
    assert len(plays_with_winner(plays, 1)) == 1


def test_total_duration():
    plays = [Play(duration_minutes=60), Play(duration_minutes=30), Play(duration_minutes=None)]
    assert total_duration(plays) == 90


def test_average_duration():
    plays = [Play(duration_minutes=60), Play(duration_minutes=30)]
    assert average_duration(plays) == 45.0


def test_average_duration_empty():
    assert average_duration([]) is None


def test_first_and_last_play():
    plays = [
        Play(game_id=1, played_at="2025-01-01"),
        Play(game_id=1, played_at="2025-06-01"),
    ]
    assert first_play(plays, 1).played_at == "2025-01-01"
    assert last_play(plays, 1).played_at == "2025-06-01"


def test_days_since_last_play():
    plays = [Play(game_id=1, played_at=date.today().isoformat())]
    assert days_since_last_play(plays, 1) == 0


def test_days_since_last_play_none():
    assert days_since_last_play([], 1) is None


def test_format_play_summary():
    p = Play(game_id=1, played_at="2025-06-01", duration_minutes=90, incomplete=True)
    s = format_play_summary(p, "Catan")
    assert "Catan" in s
    assert "90 min" in s
    assert "incomplete" in s


def test_merge_scores():
    a = Play(scores={"1": 5.0})
    b = Play(scores={"2": 10.0})
    merge_scores(a, b)
    assert a.scores == {"1": 5.0, "2": 10.0}


def test_clear_winners():
    p = Play(winner_ids=[1, 2])
    clear_winners(p)
    assert p.winner_ids == []


def test_mark_all_winners():
    p = Play(player_ids=[1, 2, 3])
    mark_all_winners(p)
    assert p.winner_ids == [1, 2, 3]


def test_plays_on_date():
    plays = [Play(played_at="2025-06-01T10:00"), Play(played_at="2025-06-02")]
    assert len(plays_on_date(plays, "2025-06-01")) == 1


def test_multi_game_sessions():
    plays = [
        Play(game_id=1, played_at="2025-06-01"),
        Play(game_id=2, played_at="2025-06-01"),
    ]
    assert multi_game_sessions(plays, "2025-06-01") == 2


def test_copy_play_template():
    orig = Play(game_id=1, player_ids=[1], notes="hi")
    copy = copy_play_template(orig, game_id=2)
    assert copy.game_id == 2
    assert copy.notes == "hi"


def test_validate_play_roster_ok():
    p = Play(player_ids=[1], winner_ids=[1])
    assert validate_play_roster(p, {1, 2}) == []


def test_validate_play_roster_unknown_player():
    p = Play(player_ids=[99])
    assert "unknown player 99" in validate_play_roster(p, {1})


def test_validate_play_roster_winner_not_seated():
    p = Play(player_ids=[1], winner_ids=[2])
    assert "winner 2 not seated" in validate_play_roster(p, {1, 2})


def test_duration_label_hours():
    assert duration_label(Play(duration_minutes=90)) == "1h 30m"


def test_duration_label_minutes_only():
    assert duration_label(Play(duration_minutes=45)) == "45m"


def test_duration_label_unknown():
    assert duration_label(Play()) == "?"
