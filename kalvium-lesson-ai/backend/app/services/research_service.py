from sqlalchemy.orm import Session

from app.agents.research_agent import ResearchAgent
from app.core.config import Settings
from app.models.research import ResearchRequest, ResearchSource


async def run_research(db: Session, settings: Settings, query: str, max_results: int) -> ResearchRequest:
    request = ResearchRequest(query=query.strip(), status="completed")
    db.add(request)
    db.flush()

    sources, errors = await ResearchAgent(settings).research(query, max_results)
    request.status = "partial" if sources and errors else "failed" if errors else "completed"
    request.error_message = "\n".join(errors) or None
    for source in sources:
        db.add(ResearchSource(request_id=request.id, **source))
    db.commit()
    db.refresh(request)
    return request
