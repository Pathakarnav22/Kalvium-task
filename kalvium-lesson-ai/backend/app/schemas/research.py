from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ResearchRequestCreate(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    max_results: int = Field(default=5, ge=1, le=10)


class ResearchSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: str
    source_type: Literal["website", "book", "youtube"]
    author_publisher: str | None = None
    description: str | None = None
    provider: str


class ResearchRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    status: Literal["completed", "partial", "failed"]
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    sources: list[ResearchSourceResponse] = []
