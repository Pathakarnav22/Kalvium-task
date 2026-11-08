from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.dependencies import get_db
from app.models.lesson import Lesson
from app.models.qc_factual import FactualQCReport
from app.schemas.qc_factual import FactualQCReportResponse
from app.services.factual_qc_service import run_factual_qc

router = APIRouter(prefix="/lessons/{lesson_id}/qc/factual", tags=["factual qc"])


@router.post("", response_model=FactualQCReportResponse, status_code=201)
async def run_qc(lesson_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    existing = db.query(FactualQCReport).filter(
        FactualQCReport.lesson_id == lesson_id,
        FactualQCReport.status == "completed",
    ).order_by(FactualQCReport.created_at.desc()).first()
    if existing is not None:
        return existing
    try:
        report = await run_factual_qc(db, settings, lesson_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if report.status == "failed":
        raise HTTPException(status_code=502, detail=report.error_message or "Factual QC failed")
    return report


@router.get("", response_model=list[FactualQCReportResponse])
def list_qc_reports(lesson_id: int, db: Session = Depends(get_db)):
    if db.get(Lesson, lesson_id) is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return db.query(FactualQCReport).filter(FactualQCReport.lesson_id == lesson_id).order_by(FactualQCReport.created_at.desc()).all()


@router.get("/{report_id}", response_model=FactualQCReportResponse)
def get_qc_report(lesson_id: int, report_id: int, db: Session = Depends(get_db)):
    report = db.get(FactualQCReport, report_id)
    if not report or report.lesson_id != lesson_id:
        raise HTTPException(status_code=404, detail="Factual QC report not found")
    return report
