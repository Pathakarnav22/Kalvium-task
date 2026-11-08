from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.dependencies import get_db
from app.models.research import ResearchRequest
from app.schemas.research import ResearchRequestCreate, ResearchRequestResponse
from app.services.research_service import run_research

router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_research(payload: ResearchRequestCreate, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Research query cannot be empty")
    return await run_research(db, settings, query, payload.max_results)


@router.get("", response_model=list[ResearchRequestResponse])
def list_research(db: Session = Depends(get_db)):
    return db.query(ResearchRequest).order_by(ResearchRequest.created_at.desc()).all()


@router.get("/{research_id}", response_model=ResearchRequestResponse)
def get_research(research_id: int, db: Session = Depends(get_db)):
    result = db.get(ResearchRequest, research_id)
    if not result:
        raise HTTPException(status_code=404, detail="Research request not found")
    return result


@router.post("/{research_id}/retry", response_model=ResearchRequestResponse)
async def retry_research(research_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    existing = db.get(ResearchRequest, research_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Research request not found")
    db.query(ResearchRequest.sources.property.mapper.class_).filter_by(request_id=research_id).delete(synchronize_session=False)
    db.commit()
    db.expire(existing, ["sources"])
    return await run_research(db, settings, existing.query, 5)
