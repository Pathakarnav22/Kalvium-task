import asyncio
from abc import ABC, abstractmethod

import httpx


class LLMProviderError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.8-flash"):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        try:
            async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
                response = await client.post(url, params={"key": self.api_key}, json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"},
                })
                response.raise_for_status()
                payload = response.json()
            text = payload["candidates"][0]["content"]["parts"][0]["text"].strip()
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json\n"):
                    text = text[5:]
                text = text.strip()
            return text
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500] if exc.response is not None else ""
            status_code = exc.response.status_code if exc.response is not None else None
            raise LLMProviderError(f"Gemini HTTP {status_code}: {body}", status_code) from exc
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMProviderError(f"Gemini request failed: {exc}") from exc


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": prompt}]},
                )
                response.raise_for_status()
                payload = response.json()
            return payload["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            raise LLMProviderError(str(exc), status_code) from exc
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMProviderError(str(exc)) from exc


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"model": self.model, "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": prompt}]},
                )
                response.raise_for_status()
                payload = response.json()
            return payload["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            body = exc.response.text[:500] if exc.response is not None else ""
            raise LLMProviderError(f"Groq HTTP {status_code}: {body}", status_code) from exc
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMProviderError(f"Groq request failed: {exc}") from exc


def create_llm_provider(settings) -> tuple[str, LLMProvider | None]:
    provider = (getattr(settings, "llm_provider", None) or settings.ai_provider or "").strip().lower()
    if provider == "gemini" and settings.gemini_api_key:
        return provider, GeminiProvider(settings.gemini_api_key, settings.gemini_model)
    if provider == "openai" and settings.openai_api_key:
        return provider, OpenAIProvider(settings.openai_api_key, settings.openai_model)
    if provider == "groq" and settings.groq_api_key:
        return provider, GroqProvider(settings.groq_api_key, settings.groq_model)
    if not provider and settings.gemini_api_key:
        return "gemini", GeminiProvider(settings.gemini_api_key, settings.gemini_model)
    if not provider and settings.openai_api_key:
        return "openai", OpenAIProvider(settings.openai_api_key, settings.openai_model)
    return provider or "none", None


async def generate_with_qc_fallback(settings, prompt: str) -> tuple[str, str, str]:
    provider_name, primary = create_llm_provider(settings)
    if primary is None:
        raise RuntimeError(f"Primary QC provider '{provider_name}' is not configured")

    try:
        if provider_name == "gemini":
            for attempt in range(3):
                try:
                    return await primary.generate(prompt), provider_name, primary.model
                except LLMProviderError as exc:
                    if exc.status_code != 503 or attempt == 2:
                        raise
                    await asyncio.sleep(1 * (2 ** attempt))
        else:
            return await primary.generate(prompt), provider_name, primary.model
    except LLMProviderError as exc:
        if exc.status_code in {401, 403}:
            raise RuntimeError(f"{provider_name} authentication failed; fallback was not used") from exc
        if exc.status_code not in {503, 429} or provider_name != "gemini" or not settings.enable_qc_fallback or not settings.groq_api_key:
            raise RuntimeError(f"{provider_name} QC request failed: {exc}") from exc

    fallback = GroqProvider(settings.groq_api_key, settings.groq_model)
    try:
        return await fallback.generate(prompt), "groq", fallback.model
    except LLMProviderError as exc:
        raise RuntimeError(f"Gemini fallback failed and Groq fallback failed: {exc}") from exc
