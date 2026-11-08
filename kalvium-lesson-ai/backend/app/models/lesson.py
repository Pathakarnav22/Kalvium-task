from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_request_id: Mapped[int | None] = mapped_column(ForeignKey("research_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    lesson_title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    learning_objective: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="generated", index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="none")
    missing_source_categories: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    generation_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
