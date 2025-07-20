"""Tests for ludolog.goal."""
from ludolog.goal import (
    Goal,
    GoalKind,
    bump_progress,
    completed_goals,
    goals_for_game,
    open_goals,
)


def test_goal_to_dict_roundtrip(sample_goal):
    restored = Goal.from_dict(sample_goal.to_dict())
    assert restored.title == "Play Catan 5x"
    assert restored.target == 5.0
    assert restored.game_id == 1


def test_pct_normal_progress(sample_goal):
    sample_goal.progress = 2.5
    assert sample_goal.pct() == 50.0


def test_pct_zero_target_returns_zero():
    goal = Goal(target=0, progress=10)
    assert goal.pct() == 0.0


def test_pct_caps_at_100():
    goal = Goal(target=5, progress=10)
    assert goal.pct() == 100.0


def test_refresh_completion_marks_done():
    goal = Goal(target=3, progress=3)
    goal.refresh_completion()
    assert goal.completed is True


def test_open_goals_excludes_completed():
    open_g = Goal(id=1, completed=False)
    done = Goal(id=2, completed=True)
    result = open_goals([open_g, done])
    assert result == [open_g]


def test_completed_goals_only_done():
    open_g = Goal(id=1, completed=False)
    done = Goal(id=2, completed=True)
    result = completed_goals([open_g, done])
    assert result == [done]


def test_goals_for_game_filters_by_game_id():
    g1 = Goal(id=1, game_id=1)
    g2 = Goal(id=2, game_id=2)
    g3 = Goal(id=3, game_id=1)
    result = goals_for_game([g1, g2, g3], 1)
    assert result == [g1, g3]


def test_bump_progress_increments_and_completes():
    goal = Goal(target=3, progress=2)
    bump_progress(goal)
    assert goal.progress == 3.0
    assert goal.completed is True


def test_bump_progress_custom_amount():
    goal = Goal(target=10, progress=0)
    bump_progress(goal, amount=2.5)
    assert goal.progress == 2.5
    assert goal.completed is False


def test_goal_kind_values():
    assert GoalKind.PLAY_COUNT.value == "play_count"
    assert GoalKind.MECHANIC.value == "mechanic"


def test_from_dict_defaults():
    goal = Goal.from_dict({"id": 9})
    assert goal.kind == GoalKind.PLAY_COUNT.value
    assert goal.completed is False


def test_refresh_completion_below_target():
    goal = Goal(target=5, progress=4)
    goal.refresh_completion()
    assert goal.completed is False


def test_goals_for_game_empty():
    assert goals_for_game([Goal(game_id=2)], 1) == []


def test_open_goals_all_completed():
    assert open_goals([Goal(completed=True)]) == []
