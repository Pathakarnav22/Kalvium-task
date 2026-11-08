import asyncio
from typing import Any

import httpx


class ProviderConfigurationError(RuntimeError):
    pass


class ProviderRequestError(RuntimeError):
    pass


async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    response = await client.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


async def request_with_retries(operation, attempts: int = 3):
    attempts = max(1, attempts)
    for attempt in range(attempts):
        try:
            return await operation()
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
            if attempt == attempts - 1:
                raise ProviderRequestError(str(exc)) from exc
            await asyncio.sleep(0.25 * (attempt + 1))


async def search_web(query: str, max_results: int, api_key: str | None, timeout: float, attempts: int = 3) -> list[dict[str, str | None]]:
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "KalviumLessonAI/1.0 (educational research integration)"},
    ) as client:
        if api_key:
            payload = await request_with_retries(lambda: _post_json(client, "https://api.tavily.com/search", {
                "api_key": api_key,
                "query": f"educational official documentation: {query}",
                "search_depth": "basic",
                "include_answer": False,
                "max_results": max_results,
            }), attempts)
            return [{
                "title": str(item.get("title") or item.get("url") or "Web source"),
                "url": str(item["url"]),
                "source_type": "website",
                "author_publisher": None,
                "description": item.get("content"),
                "provider": "tavily",
            } for item in payload.get("results", []) if item.get("url")]

        payload = await request_with_retries(lambda: _get_json(
            client,
            "https://api.crossref.org/works",
            {"query": query, "rows": max_results},
        ), attempts)
    return [{
        "title": (item.get("title") or ["Academic source"])[0],
        "url": f"https://doi.org/{item['DOI']}" if item.get("DOI") else item.get("URL"),
        "source_type": "website",
        "author_publisher": (
            ", ".join(person.get("family", "") for person in item.get("author", []) if person.get("family"))
            or item.get("publisher")
        ),
        "description": item.get("abstract"),
        "provider": "crossref",
    } for item in payload.get("message", {}).get("items", []) if item.get("DOI") or item.get("URL")]


async def _post_json(client: httpx.AsyncClient, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(url, json=payload)
    response.raise_for_status()
    return response.json()


async def search_books(query: str, max_results: int, timeout: float, attempts: int = 3) -> list[dict[str, str | None]]:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        payload = await request_with_retries(lambda: _get_json(
            client,
            "https://openlibrary.org/search.json",
            {"q": query, "limit": max_results, "fields": "key,title,author_name,publisher,first_sentence,edition_count"},
        ), attempts)

    sources = []
    for item in payload.get("docs", []):
        key = item.get("key")
        if not key:
            continue
        authors = ", ".join(item.get("author_name") or []) or None
        publishers = ", ".join(item.get("publisher") or []) or None
        first_sentence = item.get("first_sentence")
        if isinstance(first_sentence, list):
            first_sentence = first_sentence[0] if first_sentence else None
        sources.append({
            "title": item.get("title") or "Untitled book",
            "url": f"https://openlibrary.org{key}",
            "source_type": "book",
            "author_publisher": authors or publishers,
            "description": str(first_sentence) if first_sentence else None,
            "provider": "openlibrary",
        })
    return sources


async def search_youtube(query: str, max_results: int, api_key: str | None, timeout: float, attempts: int = 3) -> list[dict[str, str | None]]:
    if not api_key:
        raise ProviderConfigurationError("YOUTUBE_API_KEY is not configured")

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        payload = await request_with_retries(lambda: _get_json(
            client,
            "https://www.googleapis.com/youtube/v3/search",
            {"key": api_key, "q": f"education lesson {query}", "part": "snippet", "type": "video", "maxResults": max_results, "safeSearch": "strict", "videoEmbeddable": "true"},
        ), attempts)

    sources = []
    for item in payload.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id:
            continue
        sources.append({
            "title": snippet.get("title") or "YouTube video",
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "source_type": "youtube",
            "author_publisher": snippet.get("channelTitle"),
            "description": snippet.get("description"),
            "provider": "youtube",
        })
    return sources
