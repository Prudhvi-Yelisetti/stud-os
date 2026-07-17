"""
Badge definitions and the check that runs after XP-earning events to see
if a new badge was just earned.
"""
from sqlalchemy.orm import Session

from backend.database.models.gamification import Badge, UserBadge, Streak

BADGE_DEFINITIONS = [
    {"name": "First Steps", "description": "Complete your first task", "icon": "🌱"},
    {"name": "On a Roll", "description": "Reach a 7-day task streak", "icon": "🔥"},
    {"name": "Unstoppable", "description": "Reach a 30-day task streak", "icon": "🚀"},
    {"name": "Level 5", "description": "Reach level 5", "icon": "⭐"},
    {"name": "Level 10", "description": "Reach level 10", "icon": "🏆"},
]


def ensure_badges_seeded(db: Session) -> None:
    existing = {b.name for b in db.query(Badge).all()}
    for definition in BADGE_DEFINITIONS:
        if definition["name"] not in existing:
            db.add(Badge(**definition))
    db.commit()


def award_badge_if_new(db: Session, user_id: str, badge_name: str) -> bool:
    """Returns True if the badge was newly awarded (not already held)."""
    badge = db.query(Badge).filter(Badge.name == badge_name).first()
    if badge is None:
        return False
    already_has = (
        db.query(UserBadge)
        .filter(UserBadge.user_id == user_id, UserBadge.badge_id == badge.id)
        .first()
    )
    if already_has:
        return False
    db.add(UserBadge(user_id=user_id, badge_id=badge.id))
    db.commit()
    return True


def check_streak_badges(db: Session, user_id: str, streak: Streak) -> list[str]:
    newly_awarded = []
    if streak.current_count >= 7 and award_badge_if_new(db, user_id, "On a Roll"):
        newly_awarded.append("On a Roll")
    if streak.current_count >= 30 and award_badge_if_new(db, user_id, "Unstoppable"):
        newly_awarded.append("Unstoppable")
    return newly_awarded


def check_level_badges(db: Session, user_id: str, level: int) -> list[str]:
    newly_awarded = []
    if level >= 5 and award_badge_if_new(db, user_id, "Level 5"):
        newly_awarded.append("Level 5")
    if level >= 10 and award_badge_if_new(db, user_id, "Level 10"):
        newly_awarded.append("Level 10")
    return newly_awarded
