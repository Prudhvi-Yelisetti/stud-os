"""Level tracking derived from cumulative XP."""
from sqlalchemy.orm import Session

from backend.database.models.gamification import Level
from backend.gamification.xp_rules import level_for_xp


def get_or_create_level(db: Session, user_id: str) -> Level:
    level = db.query(Level).filter(Level.user_id == user_id).first()
    if level is None:
        level = Level(user_id=user_id, current_level=1, current_xp=0)
        db.add(level)
        db.commit()
        db.refresh(level)
    return level


def apply_xp(db: Session, user_id: str, amount: int) -> tuple[Level, bool]:
    """Add XP and recompute level. Returns (level, did_level_up)."""
    level = get_or_create_level(db, user_id)
    level.current_xp = max(0, level.current_xp + amount)
    new_level = level_for_xp(level.current_xp)
    did_level_up = new_level > level.current_level
    level.current_level = new_level
    db.commit()
    db.refresh(level)
    return level, did_level_up
