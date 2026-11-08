import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.lesson import Lesson
from app.models.qc_factual import FactualQCReport
from app.services.llm_providers import generate_with_qc_fallback


METHODOLOGY = {
    "claim_weights": {"verified": 100, "partially_supported": 55, "unsupported": 20, "unverifiable": 10, "contradicted": 0},
    "severity_deductions": {"critical": 25, "high": 15, "medium": 8, "low": 3},
    "score_rule": "Start from the mean weighted claim score, then subtract severity deductions without reducing below 0. Unsupported evidence is uncertainty, not proof that a statement is false.",
}


def calculate_factual_score(claims: list[dict[str, Any]], issues: list[dict[str, Any]]) -> tuple[int, dict[str, int]]:
    weights = METHODOLOGY["claim_weights"]
    if not claims:
        return 0, {"verified": 0, "contradicted": 0, "unsupported": 0, "partially_supported": 0, "unverifiable": 0}
    statuses = {status: sum(1 for claim in claims if claim.get("verification_status") == status) for status in weights}
    claim_score = round(sum(weights.get(claim.get("verification_status", "unverifiable"), 10) for claim in claims) / len(claims))
    deductions = METHODOLOGY["severity_deductions"]
    deduction = sum(deductions.get(issue.get("severity", "low"), 3) for issue in issues)
    return max(0, claim_score - deduction), statuses


def build_factual_qc_prompt(lesson: Lesson, sources: list[Any]) -> str:
    evidence = [{"title": source.title, "url": source.url, "source_type": source.source_type, "author_publisher": source.author_publisher, "description": source.description} for source in sources]
    return f"""Act only as a Research and Factual Accuracy QC auditor. Do not assess instructional quality, structure, engagement, or objective alignment.
Return valid JSON only.
Lesson ID: {lesson.id}
Lesson title: {lesson.lesson_title}
Learning objective: {lesson.learning_objective}
Lesson content: {json.dumps(lesson.content, ensure_ascii=False)}
Retrieved evidence: {json.dumps(evidence, ensure_ascii=False)}

Extract factual claims and verify them only against the evidence list. Never cite a URL not present in retrieved evidence.
Return:
{{
 "summary":"...",
 "claims":[{{"claim_id":"C1","statement":"...","lesson_section":"...","claim_category":"definition|technical|scientific|historical|numerical|other","verification_status":"verified|contradicted|unsupported|partially_supported|unverifiable","associated_references":[{{"title":"...","url":"...","source_type":"..."}}],"evidence_type":"direct|inference|general_knowledge|unsupported"}}],
 "issues":[{{"issue_id":"I1","problematic_statement":"...","lesson_section":"...","issue_category":"missing_reference|unsupported_claim|factual_error|contradiction|source_reliability|information_gap","severity":"critical|high|medium|low","verification_status":"verified|contradicted|unsupported|partially_supported|unverifiable","explanation":"...","supporting_evidence":"...","source_title":"...|null","source_url":"...|null","suggested_correction":"..."}}]
}}
For unsupported evidence, say it could not be verified; do not treat it as false."""


def validate_qc_payload(payload: dict[str, Any], allowed_urls: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    claims = payload.get("claims")
    issues = payload.get("issues")
    if not isinstance(claims, list) or not isinstance(issues, list):
        raise ValueError("QC response must contain claims and issues lists")
    valid_claim_statuses = {"verified", "contradicted", "unsupported", "partially_supported", "unverifiable"}
    valid_severities = {"critical", "high", "medium", "low"}
    for claim in claims:
        if claim.get("verification_status") not in valid_claim_statuses or not claim.get("claim_id") or not claim.get("statement"):
            raise ValueError("QC response contains an invalid claim")
        for ref in claim.get("associated_references", []):
            if ref.get("url") and ref["url"] not in allowed_urls:
                ref["url"] = None
                ref["citation_status"] = "unavailable"
    for issue in issues:
        if issue.get("severity") not in valid_severities or issue.get("verification_status") not in valid_claim_statuses:
            raise ValueError("QC response contains an invalid issue")
        if issue.get("source_url") and issue["source_url"] not in allowed_urls:
            issue["source_url"] = None
            issue["supporting_evidence"] = "Evidence unavailable: the cited URL was not present in retrieved research and has been removed."
    return claims, issues


async def run_factual_qc(db: Session, settings: Settings, lesson_id: int) -> FactualQCReport:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise LookupError("Lesson not found")
    report = FactualQCReport(lesson_id=lesson.id, provider="none", status="failed")
    db.add(report)
    db.flush()
    try:
        if not lesson.research_request_id:
            raise RuntimeError("Lesson has no linked research request")
        from app.models.research import ResearchRequest
        research = db.get(ResearchRequest, lesson.research_request_id)
        if research is None:
            raise RuntimeError("Linked research request not found")
        provider_name, provider = None, None
        try:
            raw, provider_name, provider_model = await generate_with_qc_fallback(settings, build_factual_qc_prompt(lesson, research.sources))
            report.provider = provider_name
            report.model = provider_model
            payload = json.loads(raw)
            claims, issues = validate_qc_payload(payload, {source.url for source in research.sources})
            report.overall_score, status_counts = calculate_factual_score(claims, issues)
            report.claims = claims
            report.issues = issues
            report.summary = payload.get("summary", "")
            report.methodology = METHODOLOGY
            report.counts = {
                **status_counts,
                "claims_checked": len(claims),
                "issues_by_severity": {severity: sum(1 for issue in issues if issue.get("severity") == severity) for severity in ("critical", "high", "medium", "low")},
            }
            report.status = "completed"
            report.error_message = None
        except json.JSONDecodeError as exc:
            raise RuntimeError("QC AI provider returned invalid JSON") from exc
    except Exception as exc:
        report.error_message = str(exc)
    db.commit()
    db.refresh(report)
    return report
