"""Personal gaming goals."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class GoalKind(str, Enum):
    PLAY_COUNT = "play_count"
    NEW_GAMES = "new_games"
    WIN_RATE = "win_rate"
    MECHANIC = "mechanic"


@dataclass
class Goal:
    id: int = 0
    kind: str = GoalKind.PLAY_COUNT.value
    title: str = ""
    target: float = 0.0
    progress: float = 0.0
    deadline: str = ""
    game_id: Optional[int] = None
    player_id: Optional[int] = None
    mechanic: str = ""
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "target": self.target,
            "progress": self.progress,
            "deadline": self.deadline,
            "game_id": self.game_id,
            "player_id": self.player_id,
            "mechanic": self.mechanic,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Goal":
        return cls(
            id=int(data.get("id", 0)),
            kind=str(data.get("kind", GoalKind.PLAY_COUNT.value)),
            title=str(data.get("title", "")),
            target=float(data.get("target", 0)),
            progress=float(data.get("progress", 0)),
            deadline=str(data.get("deadline", "")),
            game_id=data.get("game_id"),
            player_id=data.get("player_id"),
            mechanic=str(data.get("mechanic", "")),
            completed=bool(data.get("completed", False)),
        )

    def pct(self) -> float:
        if self.target <= 0:
            return 0.0
        return min(100.0, 100.0 * self.progress / self.target)

    def refresh_completion(self) -> None:
        if self.progress >= self.target and self.target > 0:
            self.completed = True


def open_goals(goals: list[Goal]) -> list[Goal]:
    return [g for g in goals if not g.completed]


def completed_goals(goals: list[Goal]) -> list[Goal]:
    return [g for g in goals if g.completed]


def goals_for_game(goals: list[Goal], game_id: int) -> list[Goal]:
    return [g for g in goals if g.game_id == game_id]


def bump_progress(goal: Goal, amount: float = 1.0) -> None:
    goal.progress += amount
    goal.refresh_completion()
