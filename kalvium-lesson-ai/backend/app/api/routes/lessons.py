from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.dependencies import get_db
from app.models.lesson import Lesson
from app.schemas.lesson import GenerateLessonRequest, LessonResponse
from app.services.lesson_generation_service import generate_lesson

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.post("/generate", response_model=LessonResponse, status_code=201)
async def generate(payload: GenerateLessonRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    lesson = await generate_lesson(db, settings, payload.lesson_title, payload.learning_objective)
    if lesson.status == "failed":
        raise HTTPException(status_code=502, detail=lesson.generation_error or "Lesson generation failed")
    return lesson


@router.get("", response_model=list[LessonResponse])
def list_lessons(db: Session = Depends(get_db)):
    return db.query(Lesson).order_by(Lesson.created_at.desc()).all()


@router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson
