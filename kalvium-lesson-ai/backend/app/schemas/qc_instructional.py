from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class InstructionalCriterion(BaseModel):
    criterion: str
    score: float
    max_score: float
    rationale: str


class InstructionalIssue(BaseModel):
    issue_id: str
    lesson_section: str
    issue_category: Literal["objective_alignment", "clarity", "logical_progression", "examples", "applications", "activity", "knowledge_check", "pacing", "missing_concept", "instructional_gap"]
    severity: Literal["critical", "high", "medium", "low"]
    explanation: str
    recommendation: str
    affected_content: str = ""


class InstructionalQCReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    qc_type: Literal["instructional_quality"]
    provider: str
    model: str = "none"
    status: Literal["completed", "failed"]
    overall_score: int
    summary: str
    methodology: dict[str, Any] = {}
    criteria_scores: list[InstructionalCriterion] = []
    issues: list[InstructionalIssue] = []
    counts: dict[str, Any] = {}
    error_message: str | None = None
    created_at: datetime
