from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class FactualClaim(BaseModel):
    claim_id: str
    statement: str
    lesson_section: str
    claim_category: str
    verification_status: Literal["verified", "contradicted", "unsupported", "partially_supported", "unverifiable"]
    associated_references: list[dict[str, Any]] = []
    evidence_type: Literal["direct", "inference", "general_knowledge", "unsupported"] = "unsupported"


class FactualIssue(BaseModel):
    issue_id: str
    problematic_statement: str
    lesson_section: str
    issue_category: str
    severity: Literal["critical", "high", "medium", "low"]
    verification_status: Literal["verified", "contradicted", "unsupported", "partially_supported", "unverifiable"]
    explanation: str
    supporting_evidence: str | None = "No sufficient evidence was retrieved."
    source_title: str | None = None
    source_url: str | None = None
    suggested_correction: str


class FactualQCReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    qc_type: Literal["factual_accuracy"]
    provider: str
    model: str = "none"
    status: Literal["completed", "failed"]
    overall_score: int
    summary: str
    methodology: dict[str, Any] = {}
    claims: list[FactualClaim] = []
    issues: list[FactualIssue] = []
    counts: dict[str, Any] = {}
    error_message: str | None = None
    created_at: datetime
