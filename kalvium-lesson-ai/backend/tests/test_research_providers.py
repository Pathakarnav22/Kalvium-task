import pytest
from unittest.mock import AsyncMock

from app.services import research_providers


class FakeAsyncClient:
    def __init__(self, response, *args, **kwargs):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def get(self, *args, **kwargs):
        return self.response

    async def post(self, *args, **kwargs):
        return self.response


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


@pytest.mark.asyncio
async def test_web_provider_normalizes_real_shape(monkeypatch):
    response = FakeResponse({"results": [{"title": "Official Python Tutorial", "url": "https://docs.python.org/3/tutorial/", "content": "Python language documentation."}]})
    monkeypatch.setattr(research_providers.httpx, "AsyncClient", lambda *args, **kwargs: FakeAsyncClient(response))

    sources = await research_providers.search_web("python", 5, "test-key", 5)

    assert sources[0]["source_type"] == "website"
    assert sources[0]["url"].startswith("https://")


@pytest.mark.asyncio
async def test_book_provider_normalizes_real_shape(monkeypatch):
    response = FakeResponse({"docs": [{"key": "/works/OL1W", "title": "Learning Python", "author_name": ["Mark Lutz"], "publisher": ["O'Reilly"], "first_sentence": ["Python is easy to learn."]}]})
    monkeypatch.setattr(research_providers.httpx, "AsyncClient", lambda *args, **kwargs: FakeAsyncClient(response))

    sources = await research_providers.search_books("python", 5, 5)

    assert sources[0]["source_type"] == "book"
    assert sources[0]["author_publisher"] == "Mark Lutz"
    assert sources[0]["url"] == "https://openlibrary.org/works/OL1W"


@pytest.mark.asyncio
async def test_youtube_provider_normalizes_real_shape(monkeypatch):
    response = FakeResponse({"items": [{"id": {"videoId": "abc123"}, "snippet": {"title": "Python Lesson", "channelTitle": "Educational Channel", "description": "A Python lesson."}}]})
    monkeypatch.setattr(research_providers.httpx, "AsyncClient", lambda *args, **kwargs: FakeAsyncClient(response))

    sources = await research_providers.search_youtube("python", 5, "test-key", 5)

    assert sources[0]["source_type"] == "youtube"
    assert sources[0]["url"] == "https://www.youtube.com/watch?v=abc123"
