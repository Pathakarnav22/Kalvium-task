import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.lesson import Lesson
from app.models.qc_instructional import InstructionalQCReport
from app.services.llm_providers import generate_with_qc_fallback


METHODOLOGY = {
    "criteria": {
        "objective_alignment": 25,
        "clarity": 15,
        "logical_progression": 15,
        "examples_and_applications": 15,
        "activity": 10,
        "knowledge_check": 10,
        "pacing_and_45_minute_fit": 10,
    },
    "calculation": "Each criterion receives a 0–100 percentage; weighted points equal percentage × criterion weight / 100. Overall score is the sum, rounded, plus severity deductions of critical 15, high 8, medium 4, low 2 capped at 30 points.",
}


def calculate_instructional_score(criteria: list[dict[str, Any]], issues: list[dict[str, Any]]) -> int:
    weights = METHODOLOGY["criteria"]
    key_map = {
        "objective_alignment": "objective_alignment", "clarity": "clarity",
        "logical_progression": "logical_progression", "examples_and_applications": "examples_and_applications",
        "activity": "activity", "knowledge_check": "knowledge_check", "pacing_and_45_minute_fit": "pacing_and_45_minute_fit",
    }
    score = 0.0
    for criterion in criteria:
        key = criterion.get("criterion")
        if key in key_map:
            percentage = max(0, min(100, float(criterion.get("score", 0))))
            score += percentage * weights[key_map[key]] / 100
    deductions = {"critical": 15, "high": 8, "medium": 4, "low": 2}
    deduction = min(30, sum(deductions.get(issue.get("severity", "low"), 2) for issue in issues))
    return max(0, min(100, round(score - deduction)))


def build_instructional_prompt(lesson: Lesson) -> str:
    return f"""Act only as an Instructional Quality auditor. Do not assess factual accuracy or source reliability.
Return valid JSON only.
Lesson title: {lesson.lesson_title}
Learning objective: {lesson.learning_objective}
Lesson content: {json.dumps(lesson.content, ensure_ascii=False)}

Evaluate objective alignment, clarity, logical progression, examples, practical applications, activity, knowledge checks, missing concepts, instructional gaps, and realistic delivery within 45 minutes.
Return:
{{
 "summary":"...",
 "criteria_scores":[{{"criterion":"objective_alignment|clarity|logical_progression|examples_and_applications|activity|knowledge_check|pacing_and_45_minute_fit","score":0,"max_score":100,"rationale":"..."}}],
 "issues":[{{"issue_id":"I1","lesson_section":"...","issue_category":"objective_alignment|clarity|logical_progression|examples|applications|activity|knowledge_check|pacing|missing_concept|instructional_gap","severity":"critical|high|medium|low","explanation":"...","recommendation":"...","affected_content":"..."}}]
}}
Score from 0 to 100. Identify genuine instructional defects; do not cite factual correctness as an instructional issue."""


def validate_instructional_payload(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    criteria = payload.get("criteria_scores")
    issues = payload.get("issues")
    valid_criteria = set(METHODOLOGY["criteria"])
    valid_severity = {"critical", "high", "medium", "low"}
    valid_categories = {"objective_alignment", "clarity", "logical_progression", "examples", "applications", "activity", "knowledge_check", "pacing", "missing_concept", "instructional_gap"}
    if not isinstance(criteria, list) or not isinstance(issues, list):
        raise ValueError("Instructional QC response must contain criteria_scores and issues lists")
    for criterion in criteria:
        if criterion.get("criterion") not in valid_criteria:
            raise ValueError("Instructional QC contains an invalid criterion")
        if not isinstance(criterion.get("score"), (int, float)) or not 0 <= criterion["score"] <= 100:
            raise ValueError("Instructional criterion score must be from 0 to 100")
    for issue in issues:
        if issue.get("severity") not in valid_severity or issue.get("issue_category") not in valid_categories:
            raise ValueError("Instructional QC contains an invalid issue")
        if not issue.get("issue_id") or not issue.get("explanation") or not issue.get("recommendation"):
            raise ValueError("Instructional issues require ID, explanation, and recommendation")
    return criteria, issues


async def run_instructional_qc(db: Session, settings: Settings, lesson_id: int) -> InstructionalQCReport:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise LookupError("Lesson not found")
    report = InstructionalQCReport(lesson_id=lesson.id, provider="none", status="failed")
    db.add(report)
    db.flush()
    try:
        try:
            raw, provider_name, provider_model = await generate_with_qc_fallback(settings, build_instructional_prompt(lesson))
            report.provider = provider_name
            report.model = provider_model
            payload = json.loads(raw)
            criteria, issues = validate_instructional_payload(payload)
            report.overall_score = calculate_instructional_score(criteria, issues)
            report.criteria_scores = criteria
            report.issues = issues
            report.summary = payload.get("summary", "")
            report.methodology = METHODOLOGY
            report.counts = {
                "criteria_checked": len(criteria),
                "issues_identified": len(issues),
                "issues_by_severity": {severity: sum(1 for issue in issues if issue.get("severity") == severity) for severity in ("critical", "high", "medium", "low")},
            }
            report.status = "completed"
            report.error_message = None
        except json.JSONDecodeError as exc:
            raise RuntimeError("Instructional QC provider returned invalid JSON") from exc
    except Exception as exc:
        report.error_message = str(exc)
    db.commit()
    db.refresh(report)
    return report
