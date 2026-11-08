from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.models.lesson import Lesson
from app.models.lesson_review import LessonEdit, RecommendationApplication
from app.schemas.lesson_review import ApplyRecommendation, LessonEditResponse, SaveLessonEdit
from app.services.lesson_export_service import markdown_export

router = APIRouter(prefix="/lessons/{lesson_id}", tags=["lesson review"])


@router.get("/edit", response_model=LessonEditResponse | None)
def get_edit(lesson_id: int, db: Session = Depends(get_db)):
    if db.get(Lesson, lesson_id) is None:
        raise HTTPException(404, "Lesson not found")
    return db.query(LessonEdit).filter(LessonEdit.lesson_id == lesson_id).order_by(LessonEdit.created_at.desc()).first()


@router.put("/edit", response_model=LessonEditResponse)
def save_edit(lesson_id: int, payload: SaveLessonEdit, db: Session = Depends(get_db)):
    if db.get(Lesson, lesson_id) is None:
        raise HTTPException(404, "Lesson not found")
    edit = LessonEdit(lesson_id=lesson_id, content=payload.content, note=payload.note)
    db.add(edit)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, "Unable to save lesson edits") from exc
    db.refresh(edit)
    return edit


@router.post("/recommendations/apply")
def apply_recommendation(lesson_id: int, payload: ApplyRecommendation, db: Session = Depends(get_db)):
    edit = db.query(LessonEdit).filter(LessonEdit.lesson_id == lesson_id).order_by(LessonEdit.created_at.desc()).first()
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(404, "Lesson not found")
    content = dict(edit.content) if edit else dict(lesson.content)
    current = content.get(payload.section)
    if isinstance(current, dict):
        content[payload.section] = {**current, "instructor_recommendation": payload.replacement}
    else:
        content[payload.section] = payload.replacement
    db.add(LessonEdit(lesson_id=lesson_id, content=content, note=f"Applied {payload.source_qc} recommendation {payload.issue_id}"))
    db.add(RecommendationApplication(lesson_id=lesson_id, source_qc=payload.source_qc, issue_id=payload.issue_id, section=payload.section, replacement=payload.replacement))
    db.commit()
    return {"status": "applied", "section": payload.section, "issue_id": payload.issue_id}


@router.get("/export.markdown")
def export_markdown(lesson_id: int, db: Session = Depends(get_db)):
    try:
        markdown = markdown_export(db, lesson_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    return Response(content=markdown, media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename=lesson-{lesson_id}.md"})
