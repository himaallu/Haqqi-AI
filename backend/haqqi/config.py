"""Runtime settings, read from environment variables (see .env.example)."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Primary LLM: K2 Horizon hosted API (OpenAI-compatible).
    k2_api_key: SecretStr | None = None
    k2_base_url: str = "https://api.ifm.ai/v1"
    k2_model: str = "IFM/K2-Horizon-375B-A23B"

    # Backup LLM and speech-to-text: Groq free tier (OpenAI-compatible).
    groq_api_key: SecretStr | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"

    database_url: str | None = None
    cors_origins: list[str] = ["http://localhost:3000"]
    git_sha: str = "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()
