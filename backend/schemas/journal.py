from datetime import datetime, date

from pydantic import BaseModel, ConfigDict

from backend.database.models.journal import Mood


class JournalEntryCreate(BaseModel):
    title: str
    content: str = ""
    mood: Mood | None = None
    entry_date: date


class JournalEntryUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    mood: Mood | None = None


class JournalEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: str
    mood: Mood | None
    entry_date: date
    created_at: datetime
    updated_at: datetime
