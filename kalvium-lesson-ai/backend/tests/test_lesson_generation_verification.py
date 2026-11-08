import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.research import ResearchRequest, ResearchSource
from app.services.lesson_generation_service import generate_lesson


def complete_content(title: str):
    return {
        "lesson_overview": {"lesson_title": title, "learning_objective": "Learn the topic", "target_learner_level": "Beginner", "prerequisites": ["Basic knowledge"], "estimated_total_duration": 43},
        "introduction": {"duration_minutes": 3, "content": "Introduction", "why_it_matters": "It matters", "real_world_context": "Real world"},
        "core_concepts": [{"title": "Core concept", "duration_minutes": 15, "explanation": "Explanation", "example": "Example"}],
        "step_by_step_examples": [{"title": "Example", "duration_minutes": 8, "steps": [{"number": 1, "instruction": "Start", "explanation": "Explain", "code": ""}]}],
        "real_world_applications": {"duration_minutes": 5, "applications": [{"scenario": "Production", "application": "Use it"}]},
        "practical_activity": {"duration_minutes": 7, "instructions": ["Complete the task"], "expected_outcomes": ["Understanding"], "completion_time_minutes": 7},
        "knowledge_check": {"duration_minutes": 3, "questions": [{"question": "Question", "type": "short_answer", "options": [], "answer": "Answer", "explanation": "Reason"} for _ in range(3)]},
        "summary": {"duration_minutes": 2, "key_points": ["Key concept"], "objective_reinforcement": "Objective met"},
        "supplementary_resources": {"youtube": [{"title": "Verified video", "url": "https://youtube.com/watch?v=verified"}], "books": [{"title": "Verified book", "url": "https://openlibrary.org/works/verified"}], "websites": [{"title": "Verified site", "url": "https://example.com/verified"}]},
        "references": [{"title": "Verified video", "url": "https://youtube.com/watch?v=verified", "source_type": "youtube"}, {"title": "Verified book", "url": "https://openlibrary.org/works/verified", "source_type": "book"}, {"title": "Verified site", "url": "https://example.com/verified", "source_type": "website"}],
    }


def research_with_sources():
    request = ResearchRequest(query="test", status="completed")
    request.sources = [
        ResearchSource(title="Verified video", url="https://youtube.com/watch?v=verified", source_type="youtube", provider="youtube"),
        ResearchSource(title="Verified book", url="https://openlibrary.org/works/verified", source_type="book", provider="openlibrary"),
        ResearchSource(title="Verified site", url="https://example.com/verified", source_type="website", provider="tavily"),
    ]
    return request


class MockProvider:
    def __init__(self, raw):
        self.raw = raw

    async def generate(self, prompt: str):
        return self.raw


@pytest.mark.asyncio
@pytest.mark.parametrize("title", ["HTTP Requests and Responses", "Python Asyncio Fundamentals"])
async def test_verified_generation_pipeline_persists_and_versioning(title):
    db = SessionLocal()
    settings = SimpleNamespace()
    research = research_with_sources()
    content = complete_content(title)
    try:
        with patch("app.services.lesson_generation_service.run_research", return_value=research), patch("app.services.lesson_generation_service.create_llm_provider", return_value=("mock-gemini", MockProvider(json.dumps(content)))):
            first = await generate_lesson(db, settings, title, "Understand and apply the topic")
            second = await generate_lesson(db, settings, title, "Understand and apply the topic")
        assert first.status == second.status == "generated"
        assert first.content["lesson_overview"]["estimated_total_duration"] <= 45
        matching = db.query(__import__('app.models.lesson', fromlist=['Lesson']).Lesson).filter_by(lesson_title=title).all()
        assert len(matching) >= 2
        assert first.id != second.id
        assert research.sources[0].source_type == "youtube"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_invalid_ai_json_is_saved_as_failed():
    db = SessionLocal()
    research = research_with_sources()
    settings = SimpleNamespace()
    with patch("app.services.lesson_generation_service.run_research", return_value=research), patch("app.services.lesson_generation_service.create_llm_provider", return_value=("mock-gemini", MockProvider("not-json"))):
        lesson = await generate_lesson(db, settings, "Invalid JSON Test", "Test invalid AI response")
    assert lesson.status == "failed"
    assert "invalid JSON" in lesson.generation_error
    db.close()
