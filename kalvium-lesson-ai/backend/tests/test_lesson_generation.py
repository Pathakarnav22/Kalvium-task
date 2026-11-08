from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.research import ResearchRequest, ResearchSource

client = TestClient(app)


def test_blank_lesson_inputs_are_rejected():
    response = client.post('/lessons/generate', json={'lesson_title': '   ', 'learning_objective': 'Learn'})
    assert response.status_code == 422


def test_lesson_duration_is_limited():
    from app.services.lesson_generation_service import validate_content
    research = ResearchRequest(query='test')
    research.sources = [ResearchSource(title='Source', url='https://example.com', source_type='website', provider='test')]
    content = {
        'lesson_overview': {}, 'introduction': {'duration_minutes': 46}, 'core_concepts': [],
        'step_by_step_examples': [], 'real_world_applications': {}, 'practical_activity': {},
        'knowledge_check': {'questions': [{}, {}, {}]}, 'summary': {}, 'supplementary_resources': {}, 'references': []
    }
    try:
        validate_content(content, research)
    except ValueError as exc:
        assert '45 minutes' in str(exc)
    else:
        raise AssertionError('Duration limit was not enforced')


def test_reference_must_exist_in_research():
    from app.services.lesson_generation_service import validate_content
    research = ResearchRequest(query='test')
    research.sources = [ResearchSource(title='Source', url='https://example.com', source_type='website', provider='test')]
    content = {
        'lesson_overview': {'estimated_total_duration': 45}, 'introduction': {'duration_minutes': 3}, 'core_concepts': [],
        'step_by_step_examples': [], 'real_world_applications': {}, 'practical_activity': {},
        'knowledge_check': {'questions': [{}, {}, {}]}, 'summary': {}, 'supplementary_resources': {},
        'references': [{'url': 'https://made-up.example'}]
    }
    try:
        validate_content(content, research)
    except ValueError as exc:
        assert 'not present' in str(exc)
    else:
        raise AssertionError('Fabricated reference was accepted')
