from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class ChapterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    notebook_id: str
    title: str
    content: str
    pinned: bool
    version: int
    created_at: datetime
    updated_at: datetime


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
