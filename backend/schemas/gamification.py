from pydantic import BaseModel, ConfigDict


class BadgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str
    icon: str


class StreakOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    streak_type: str
    current_count: int
    longest_count: int


class GamificationProfileOut(BaseModel):
    current_level: int
    current_xp: int
    xp_to_next_level: int
    streaks: list[StreakOut]
    badges: list[BadgeOut]
