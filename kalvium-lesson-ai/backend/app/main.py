from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.health import router as health_router
from app.api.routes.research import router as research_router
from app.api.routes.lessons import router as lessons_router
from app.api.routes.qc_factual import router as qc_factual_router
from app.api.routes.qc_instructional import router as qc_instructional_router
from app.api.routes.lesson_review import router as lesson_review_router
from app.core.config import get_settings
from app.database.session import Base, engine
import app.models.research  # noqa: F401
import app.models.lesson  # noqa: F401
import app.models.qc_factual  # noqa: F401
import app.models.qc_instructional  # noqa: F401
import app.models.lesson_review  # noqa: F401

settings = get_settings()
Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, debug=settings.debug)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(research_router)
app.include_router(lessons_router)
app.include_router(qc_factual_router)
app.include_router(qc_instructional_router)
app.include_router(lesson_review_router)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(_request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=503, content={"detail": "Database service unavailable"})


@app.on_event("startup")
def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Kalvium Lesson AI API", "status": "running"}
