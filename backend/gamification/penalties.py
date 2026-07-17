"""Penalty application for overdue/missed tasks."""
from sqlalchemy.orm import Session

from backend.database.models.gamification import Penalty
from backend.gamification.xp_rules import PENALTY_FOR_OVERDUE_TASK
from backend.gamification.levels import apply_xp


def apply_overdue_penalty(db: Session, user_id: str, task_id: str) -> Penalty:
    penalty = Penalty(
        user_id=user_id,
        task_id=task_id,
        amount=PENALTY_FOR_OVERDUE_TASK,
        reason="Task went overdue",
    )
    db.add(penalty)
    db.commit()
    db.refresh(penalty)
    apply_xp(db, user_id, -PENALTY_FOR_OVERDUE_TASK)
    return penalty
