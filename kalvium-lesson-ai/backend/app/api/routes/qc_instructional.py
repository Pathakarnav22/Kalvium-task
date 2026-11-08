from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.dependencies import get_db
from app.models.lesson import Lesson
from app.models.qc_instructional import InstructionalQCReport
from app.schemas.qc_instructional import InstructionalQCReportResponse
from app.services.instructional_qc_service import run_instructional_qc

router = APIRouter(prefix="/lessons/{lesson_id}/qc/instructional", tags=["instructional qc"])


@router.post("", response_model=InstructionalQCReportResponse, status_code=201)
async def run_qc(lesson_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        report = await run_instructional_qc(db, settings, lesson_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if report.status == "failed":
        raise HTTPException(status_code=502, detail=report.error_message or "Instructional QC failed")
    return report


@router.get("", response_model=list[InstructionalQCReportResponse])
def list_qc_reports(lesson_id: int, db: Session = Depends(get_db)):
    if db.get(Lesson, lesson_id) is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return db.query(InstructionalQCReport).filter(InstructionalQCReport.lesson_id == lesson_id).order_by(InstructionalQCReport.created_at.desc()).all()


@router.get("/{report_id}", response_model=InstructionalQCReportResponse)
def get_qc_report(lesson_id: int, report_id: int, db: Session = Depends(get_db)):
    report = db.get(InstructionalQCReport, report_id)
    if not report or report.lesson_id != lesson_id:
        raise HTTPException(status_code=404, detail="Instructional QC report not found")
    return report


@router.post("", response_model=InstructionalQCReportResponse, status_code=201)
async def run_qc(lesson_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    existing = db.query(InstructionalQCReport).filter(
        InstructionalQCReport.lesson_id == lesson_id,
        InstructionalQCReport.status == "completed",
    ).order_by(InstructionalQCReport.created_at.desc()).first()
    if existing is not None:
        return existing
    try:
        report = await run_instructional_qc(db, settings, lesson_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if report.status == "failed":
        raise HTTPException(status_code=502, detail=report.error_message or "Instructional QC failed")
    return report
