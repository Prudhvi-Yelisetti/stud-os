"""
XP awards and level thresholds. Kept as pure functions/constants so the
engine (which touches the DB) stays simple and this stays unit-testable.
"""
from backend.database.models.tasks import TaskPriority

XP_FOR_TASK_COMPLETION = {
    TaskPriority.low: 5,
    TaskPriority.medium: 10,
    TaskPriority.high: 20,
    TaskPriority.urgent: 30,
}

PENALTY_FOR_OVERDUE_TASK = 5

XP_PER_LEVEL = 100  # flat threshold for V1; make this curved later if needed


def level_for_xp(total_xp: int) -> int:
    return max(1, (total_xp // XP_PER_LEVEL) + 1)
