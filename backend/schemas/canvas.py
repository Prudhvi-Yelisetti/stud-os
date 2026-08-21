import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class CanvasCreate(BaseModel):
    title: str


class CanvasUpdate(BaseModel):
    title: str | None = None
    data: str | None = None

    @field_validator("data")
    @classmethod
    def data_must_be_valid_json(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError("data must be valid JSON") from e
        return v


class CanvasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    data: str
    created_at: datetime
    updated_at: datetime
