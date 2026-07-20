"""
The single entry point routers call when a gamification-relevant event
happens. Keeps XP/levels/streaks/badges wiring out of the task router.
"""
from sqlalchemy.orm import Session

from backend.database.models.gamification import XPLog, Level, Streak
from backend.database.models.tasks import TaskPriority
from backend.gamification.xp_rules import XP_FOR_TASK_COMPLETION
from backend.gamification.levels import apply_xp
from backend.gamification.streaks import record_activity
from backend.gamification.badges import (
    award_badge_if_new, check_streak_badges, check_level_badges, ensure_badges_seeded,
)


class GamificationResult:
    def __init__(
        self,
        xp_awarded: int,
        level: Level,
        did_level_up: bool,
        streak: Streak,
        newly_awarded_badges: list[str],
    ):
        self.xp_awarded = xp_awarded
        self.level = level
        self.did_level_up = did_level_up
        self.streak = streak
        self.newly_awarded_badges = newly_awarded_badges


def on_task_completed(db: Session, user_id: str, priority: TaskPriority) -> GamificationResult:
    # Badges may never have been seeded if the user has never opened the
    # gamification profile view -- seed defensively here too, since badge
    # awards can happen from task completion without that page ever loading.
    ensure_badges_seeded(db)

    xp_amount = XP_FOR_TASK_COMPLETION[priority]

    db.add(XPLog(user_id=user_id, amount=xp_amount, reason=f"Completed a {priority.value} priority task"))
    db.commit()

    level, did_level_up = apply_xp(db, user_id, xp_amount)
    streak = record_activity(db, user_id)

    newly_awarded: list[str] = []
    if award_badge_if_new(db, user_id, "First Steps"):
        newly_awarded.append("First Steps")
    newly_awarded += check_streak_badges(db, user_id, streak)
    if did_level_up:
        newly_awarded += check_level_badges(db, user_id, level.current_level)

    return GamificationResult(
        xp_awarded=xp_amount,
        level=level,
        did_level_up=did_level_up,
        streak=streak,
        newly_awarded_badges=newly_awarded,
    )
