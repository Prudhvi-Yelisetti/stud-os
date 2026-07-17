"""Daily task-completion streak tracking."""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from backend.database.models.gamification import Streak

STREAK_TYPE_TASKS = "daily_tasks"


def record_activity(db: Session, user_id: str, streak_type: str = STREAK_TYPE_TASKS) -> Streak:
    today = date.today()
    streak = (
        db.query(Streak)
        .filter(Streak.user_id == user_id, Streak.streak_type == streak_type)
        .first()
    )
    if streak is None:
        streak = Streak(
            user_id=user_id, streak_type=streak_type, current_count=1, longest_count=1, last_active_date=today
        )
        db.add(streak)
        db.commit()
        db.refresh(streak)
        return streak

    if streak.last_active_date == today:
        return streak  # already counted today

    if streak.last_active_date == today - timedelta(days=1):
        streak.current_count += 1
    else:
        streak.current_count = 1  # streak broken, restart

    streak.longest_count = max(streak.longest_count, streak.current_count)
    streak.last_active_date = today
    db.commit()
    db.refresh(streak)
    return streak
