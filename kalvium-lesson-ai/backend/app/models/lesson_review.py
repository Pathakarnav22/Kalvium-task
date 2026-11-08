from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class LessonEdit(Base):
    __tablename__ = "lesson_edits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RecommendationApplication(Base):
    __tablename__ = "recommendation_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    source_qc: Mapped[str] = mapped_column(String(30), nullable=False)
    issue_id: Mapped[str] = mapped_column(String(100), nullable=False)
    section: Mapped[str] = mapped_column(String(100), nullable=False)
    replacement: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
