from datetime import date

from pydantic import BaseModel, ConfigDict


class LevelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_level: int
    current_xp: int


class StreakOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    streak_type: str
    current_count: int
    longest_count: int
    last_active_date: date | None


class BadgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str
    icon: str


class ProfileOut(BaseModel):
    level: LevelOut
    streaks: list[StreakOut]
    badges: list[BadgeOut]
