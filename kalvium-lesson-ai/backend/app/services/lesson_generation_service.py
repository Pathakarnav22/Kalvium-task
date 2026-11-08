import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.lesson import Lesson
from app.models.research import ResearchRequest
from app.services.llm_providers import LLMProviderError, create_llm_provider
from app.services.research_service import run_research


def build_prompt(lesson_title: str, objective: str, research_request: ResearchRequest) -> str:
    sources = [{
        "title": source.title,
        "url": source.url,
        "source_type": source.source_type,
        "author_publisher": source.author_publisher,
        "description": source.description,
    } for source in research_request.sources]
    return f"""Create a complete lesson as valid JSON only. Do not include Markdown fences.
Lesson title: {lesson_title}
Learning objective: {objective}

Use ONLY these retrieved sources. Never invent titles, authors, publishers, URLs, or videos.
Retrieved sources: {json.dumps(sources, ensure_ascii=False)}

Required JSON shape:
{{
  "lesson_overview": {{"lesson_title":"...","learning_objective":"...","target_learner_level":"...","prerequisites":["..."],"estimated_total_duration":45}},
  "introduction": {{"duration_minutes":3,"why_it_matters":"...","real_world_context":"...","content":"..."}},
  "core_concepts": [{{"title":"...","duration_minutes":15,"explanation":"...","example":"..."}}],
  "step_by_step_examples": [{{"title":"...","duration_minutes":8,"steps":[{{"number":1,"instruction":"...","explanation":"...","code":"..."}}]}}],
  "real_world_applications": {{"duration_minutes":5,"applications":[{{"scenario":"...","application":"..."}}]}},
  "practical_activity": {{"duration_minutes":7,"instructions":["..."],"expected_outcomes":["..."],"completion_time_minutes":7}},
  "knowledge_check": {{"duration_minutes":3,"questions":[{{"question":"...","type":"multiple_choice","options":["..."],"answer":"...","explanation":"..."}}]}},
  "summary": {{"duration_minutes":2,"key_points":["..."],"objective_reinforcement":"..."}},
  "supplementary_resources": {{"youtube":[{{"title":"...","url":"..."}}],"books":[{{"title":"...","url":"..."}}],"websites":[{{"title":"...","url":"..."}}]}},
  "references": [{{"title":"...","url":"...","source_type":"website|book|youtube","author_publisher":"...","description":"..."}}]
}}
Generate 3 knowledge-check questions and keep the sum of all duration_minutes fields, excluding nested prerequisite or activity metadata, at or below 45."""


def validate_content(content: dict[str, Any], research_request: ResearchRequest) -> dict[str, Any]:
    allowed_urls = {source.url for source in research_request.sources}
    required_sections = ["lesson_overview", "introduction", "core_concepts", "step_by_step_examples", "real_world_applications", "practical_activity", "knowledge_check", "summary", "supplementary_resources", "references"]
    missing = [section for section in required_sections if section not in content]
    if missing:
        raise ValueError(f"Generated lesson is missing sections: {', '.join(missing)}")

    duration_values = []
    overview_duration = content.get("lesson_overview", {}).get("estimated_total_duration")
    if not isinstance(overview_duration, (int, float)) or overview_duration < 0 or overview_duration > 45:
        raise ValueError("Lesson overview duration must be between 0 and 45 minutes")
    for section in ["introduction", "real_world_applications", "practical_activity", "knowledge_check", "summary"]:
        duration = content.get(section, {}).get("duration_minutes")
        if isinstance(duration, (int, float)):
            duration_values.append(duration)
    duration_values.extend(concept.get("duration_minutes", 0) for concept in content.get("core_concepts", []) if isinstance(concept, dict))
    duration_values.extend(example.get("duration_minutes", 0) for example in content.get("step_by_step_examples", []) if isinstance(example, dict))
    if sum(duration_values) > 45:
        raise ValueError("Generated lesson exceeds 45 minutes")

    references = content.get("references", [])
    verified_references = [reference for reference in references if reference.get("url") in allowed_urls]
    if len(verified_references) != len(references):
        raise ValueError("Generated lesson contains a reference not present in retrieved research")

    questions = content.get("knowledge_check", {}).get("questions", [])
    if not 3 <= len(questions) <= 5:
        raise ValueError("Knowledge check must contain 3 to 5 questions")

    resources = content.get("supplementary_resources", {})
    resource_urls = []
    for category in ("youtube", "books", "websites"):
        resource_urls.extend(resource.get("url") for resource in resources.get(category, []) if isinstance(resource, dict))
    invalid_resource_urls = [url for url in resource_urls if url not in allowed_urls]
    if invalid_resource_urls:
        raise ValueError("Generated supplementary resources contain URLs not present in retrieved research")
    return content


async def generate_lesson(db: Session, settings: Settings, lesson_title: str, learning_objective: str) -> Lesson:
    lesson = Lesson(lesson_title=lesson_title, learning_objective=learning_objective, status="failed")
    db.add(lesson)
    db.flush()
    try:
        query = f"{lesson_title}. {learning_objective}"
        research_request = await run_research(db, settings, query, 5)
        lesson.research_request_id = research_request.id
        present_types = {source.source_type for source in research_request.sources}
        lesson.missing_source_categories = sorted({"website", "book", "youtube"} - present_types)
        if not research_request.sources:
            raise RuntimeError("Research failed and returned no usable sources")

        provider_name, provider = create_llm_provider(settings)
        lesson.provider = provider_name
        if provider is None:
            raise RuntimeError("No AI provider configured: set AI_PROVIDER with GEMINI_API_KEY or OPENAI_API_KEY")

        try:
            raw = await provider.generate(build_prompt(lesson_title, learning_objective, research_request))
            content = json.loads(raw)
            lesson.content = validate_content(content, research_request)
            lesson.status = "generated"
            lesson.generation_error = None
        except LLMProviderError as exc:
            raise RuntimeError(f"AI provider request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("AI provider returned invalid JSON") from exc
    except Exception as exc:
        lesson.generation_error = str(exc)
    db.commit()
    db.refresh(lesson)
    return lesson
