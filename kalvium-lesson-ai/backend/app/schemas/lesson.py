from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GenerateLessonRequest(BaseModel):
    lesson_title: str = Field(min_length=1, max_length=200)
    learning_objective: str = Field(min_length=1, max_length=1000)

    @field_validator("lesson_title", "learning_objective")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty or whitespace-only")
        return value


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    research_request_id: int | None
    lesson_title: str
    learning_objective: str
    status: Literal["generated", "failed"]
    provider: str
    missing_source_categories: list[str] = []
    generation_error: str | None = None
    content: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
