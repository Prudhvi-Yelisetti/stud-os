from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, computed_field

from backend.utils.frontmatter import parse_frontmatter
from backend.utils.tags import extract_tags


class NotebookCreate(BaseModel):
    title: str
    description: str | None = None


class NotebookUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class NotebookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class ChapterCreate(BaseModel):
    title: str
    content: str = ""


class ChapterUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    pinned: bool | None = None
    is_template: bool | None = None
    is_daily_template: bool | None = None


class ChapterPropertiesUpdate(BaseModel):
    properties: dict[str, Any]


class ChapterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    notebook_id: str
    title: str
    content: str
    pinned: bool
    version: int
    is_template: bool
    is_daily_template: bool
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def properties(self) -> dict:
        """Parsed from the frontmatter block at the top of `content` --
        not a stored column, content is the single source of truth (same
        philosophy as Obsidian keeping frontmatter in the .md file)."""
        properties, _ = parse_frontmatter(self.content)
        return properties

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tags(self) -> list[str]:
        properties, body = parse_frontmatter(self.content)
        return sorted(extract_tags(body, properties))


class BacklinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str


class ChapterTitleMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    notebook_id: str


class ChapterVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version_number: int
    content_snapshot: str
    created_at: datetime
