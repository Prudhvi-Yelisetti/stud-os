from datetime import datetime, date
from typing import Any

from pydantic import BaseModel, ConfigDict, computed_field

from backend.database.models.journal import Mood
from backend.utils.frontmatter import parse_frontmatter
from backend.utils.tags import extract_tags


class JournalEntryCreate(BaseModel):
    title: str
    content: str = ""
    mood: Mood | None = None
    entry_date: date


class JournalEntryUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    mood: Mood | None = None


class JournalEntryPropertiesUpdate(BaseModel):
    properties: dict[str, Any]


class JournalEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: str
    mood: Mood | None
    entry_date: date
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def properties(self) -> dict:
        properties, _ = parse_frontmatter(self.content)
        return properties

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tags(self) -> list[str]:
        properties, body = parse_frontmatter(self.content)
        return sorted(extract_tags(body, properties))
