from datetime import datetime, timezone

from backend.database.models.tasks import RepeatRule
from backend.utils.recurrence import next_occurrence


def test_daily_adds_one_day():
    base = datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc)
    result = next_occurrence(RepeatRule.daily, base)
    assert result == datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)


def test_weekly_adds_seven_days():
    base = datetime(2026, 7, 19, tzinfo=timezone.utc)
    result = next_occurrence(RepeatRule.weekly, base)
    assert result == datetime(2026, 7, 26, tzinfo=timezone.utc)


def test_monthly_adds_thirty_days():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = next_occurrence(RepeatRule.monthly, base)
    assert result == datetime(2026, 1, 31, tzinfo=timezone.utc)


def test_none_repeat_rule_returns_none():
    assert next_occurrence(RepeatRule.none, datetime.now(timezone.utc)) is None
