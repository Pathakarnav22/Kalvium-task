from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SaveLessonEdit(BaseModel):
    content: dict[str, Any]
    note: str | None = Field(default=None, max_length=500)


class ApplyRecommendation(BaseModel):
    source_qc: Literal["factual", "instructional"]
    issue_id: str = Field(min_length=1, max_length=100)
    section: str = Field(min_length=1, max_length=100)
    replacement: str = Field(min_length=1, max_length=10000)


class LessonEditResponse(BaseModel):
    id: int
    lesson_id: int
    content: dict[str, Any]
    note: str | None = None
    created_at: datetime
