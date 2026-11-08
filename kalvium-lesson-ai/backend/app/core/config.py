from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Kalvium Lesson AI API"
    database_url: str = "sqlite:///./kalvium.db"
    frontend_url: str = "http://localhost:5173"
    debug: bool = False
    tavily_api_key: str | None = None
    youtube_api_key: str | None = None
    research_timeout_seconds: float = 15.0
    research_retry_attempts: int = 3
    ai_provider: str | None = None
    llm_provider: str = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    enable_qc_fallback: bool = True
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
