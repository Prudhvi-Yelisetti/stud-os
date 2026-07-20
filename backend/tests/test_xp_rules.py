from backend.gamification.xp_rules import level_for_xp, XP_PER_LEVEL, XP_FOR_TASK_COMPLETION
from backend.database.models.tasks import TaskPriority


def test_zero_xp_is_level_one():
    assert level_for_xp(0) == 1


def test_negative_xp_clamps_to_level_one():
    assert level_for_xp(-50) == 1


def test_exactly_one_threshold_reaches_level_two():
    assert level_for_xp(XP_PER_LEVEL) == 2


def test_just_under_threshold_stays_level_one():
    assert level_for_xp(XP_PER_LEVEL - 1) == 1


def test_xp_awards_increase_with_priority():
    values = [XP_FOR_TASK_COMPLETION[p] for p in
              (TaskPriority.low, TaskPriority.medium, TaskPriority.high, TaskPriority.urgent)]
    assert values == sorted(values), "higher priority should never award less XP"
