from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.user import User
from backend.database.models.gamification import Streak, Badge, UserBadge
from backend.dependencies import get_current_user
from backend.gamification.levels import get_or_create_level
from backend.gamification.badges import ensure_badges_seeded
from backend.schemas.gamification import ProfileOut, LevelOut, StreakOut, BadgeOut

router = APIRouter(prefix="/api/gamification", tags=["gamification"])


@router.get("/profile", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_badges_seeded(db)
    level = get_or_create_level(db, user.id)
    streaks = db.query(Streak).filter(Streak.user_id == user.id).all()
    earned_badges = (
        db.query(Badge)
        .join(UserBadge, UserBadge.badge_id == Badge.id)
        .filter(UserBadge.user_id == user.id)
        .all()
    )
    return ProfileOut(
        level=LevelOut.model_validate(level),
        streaks=[StreakOut.model_validate(s) for s in streaks],
        badges=[BadgeOut.model_validate(b) for b in earned_badges],
    )
