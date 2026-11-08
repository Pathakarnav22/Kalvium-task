import asyncio
from collections.abc import Callable
from typing import Any

from app.core.config import Settings
from app.services.research_providers import (
    ProviderConfigurationError,
    ProviderRequestError,
    search_books,
    search_web,
    search_youtube,
)


class ResearchAgent:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def research(self, query: str, max_results: int) -> tuple[list[dict[str, Any]], list[str]]:
        jobs: list[tuple[str, Callable[..., object]]] = [
            ("website", lambda: search_web(query, max_results, self.settings.tavily_api_key, self.settings.research_timeout_seconds, self.settings.research_retry_attempts)),
            ("book", lambda: search_books(query, max_results, self.settings.research_timeout_seconds, self.settings.research_retry_attempts)),
            ("youtube", lambda: search_youtube(query, max_results, self.settings.youtube_api_key, self.settings.research_timeout_seconds, self.settings.research_retry_attempts)),
        ]
        results = await asyncio.gather(*(job() for _, job in jobs), return_exceptions=True)

        sources: list[dict[str, Any]] = []
        errors: list[str] = []
        seen_urls: set[str] = set()
        for (source_type, _job), result in zip(jobs, results):
            if isinstance(result, ProviderConfigurationError):
                errors.append(f"{source_type}: {result}")
                continue
            if isinstance(result, ProviderRequestError):
                errors.append(f"{source_type}: provider request failed: {result}")
                continue
            if isinstance(result, Exception):
                errors.append(f"{source_type}: unexpected provider error: {result}")
                continue
            for source in result:
                url = source["url"]
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    sources.append(source)
        return sources, errors
