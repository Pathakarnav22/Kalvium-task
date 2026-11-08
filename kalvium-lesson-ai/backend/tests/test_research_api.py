from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_empty_research_is_rejected():
    response = client.post("/research", json={"query": "  "})
    assert response.status_code == 422


def test_missing_research_is_404():
    response = client.get("/research/999999")
    assert response.status_code == 404


def test_research_persists_normalized_sources():
    sources = [{
        "title": "Official Python tutorial",
        "url": "https://docs.python.org/3/tutorial/",
        "source_type": "website",
        "author_publisher": None,
        "description": "The official Python tutorial.",
        "provider": "test",
    }]
    with patch("app.services.research_service.ResearchAgent.research", return_value=(sources, [])):
        response = client.post("/research", json={"query": "Python basics", "max_results": 5})
    assert response.status_code == 201
    body = response.json()
    assert body["query"] == "Python basics"
    assert body["status"] == "completed"
    assert body["sources"][0]["url"] == "https://docs.python.org/3/tutorial/"
