"""Computes the next occurrence date for a recurring task."""
from datetime import datetime, timedelta

from backend.database.models.tasks import RepeatRule

_INTERVALS = {
    RepeatRule.daily: timedelta(days=1),
    RepeatRule.weekly: timedelta(days=7),
    RepeatRule.monthly: timedelta(days=30),  # simple approximation, not calendar-aware
}


def next_occurrence(repeat_rule: RepeatRule, base: datetime) -> datetime | None:
    """Returns the next occurrence datetime, or None if repeat_rule is 'none'."""
    interval = _INTERVALS.get(repeat_rule)
    if interval is None:
        return None
    return base + interval
