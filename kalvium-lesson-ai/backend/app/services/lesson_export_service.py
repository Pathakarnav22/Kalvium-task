import json
from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.lesson_review import LessonEdit
from app.models.qc_factual import FactualQCReport
from app.models.qc_instructional import InstructionalQCReport
from app.models.research import ResearchRequest


def markdown_export(db: Session, lesson_id: int) -> str:
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise LookupError("Lesson not found")
    edit = db.query(LessonEdit).filter(LessonEdit.lesson_id == lesson_id).order_by(LessonEdit.created_at.desc()).first()
    content = edit.content if edit else lesson.content
    factual = db.query(FactualQCReport).filter(FactualQCReport.lesson_id == lesson_id).order_by(FactualQCReport.created_at.desc()).first()
    instructional = db.query(InstructionalQCReport).filter(InstructionalQCReport.lesson_id == lesson_id).order_by(InstructionalQCReport.created_at.desc()).first()
    lines = [f"# {lesson.lesson_title}", "", f"**Learning objective:** {lesson.learning_objective}", "", "## Lesson", "", "```json", json.dumps(content, indent=2, ensure_ascii=False), "```", "", "## References"]
    research = db.get(ResearchRequest, lesson.research_request_id) if lesson.research_request_id else None
    if research:
        for source in research.sources:
            lines.append(f"- {source.title} ({source.source_type}) — {source.url}")
    else:
        lines.append("- No linked research references.")
    for heading, report in [("QC Agent 1 — Research and Factual Accuracy", factual), ("QC Agent 2 — Instructional Quality", instructional)]:
        lines += ["", f"## {heading}", ""]
        if not report:
            lines.append("No report generated.")
        else:
            lines += [f"- Status: {report.status}", f"- Overall score: {report.overall_score}", f"- Summary: {report.summary}", "", "### Issues"]
            for issue in report.issues:
                lines.append(f"- **{issue.get('issue_id', 'issue')}** ({issue.get('severity', 'unknown')}): {issue.get('explanation') or issue.get('supporting_evidence', '')}")
                if issue.get('recommendation'):
                    lines.append(f"  - Recommendation: {issue['recommendation']}")
                elif issue.get('suggested_correction'):
                    lines.append(f"  - Suggested correction: {issue['suggested_correction']}")
    return "\n".join(lines) + "\n"
