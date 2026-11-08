from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class InstructionalQCReport(Base):
    __tablename__ = "instructional_qc_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    qc_type: Mapped[str] = mapped_column(String(50), nullable=False, default="instructional_quality")
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="none")
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="none")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="completed", index=True)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    methodology: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    criteria_scores: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    issues: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    counts: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
