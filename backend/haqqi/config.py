"""Runtime settings, read from environment variables (see .env.example)."""

import json
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM: Gemini (free tier, OpenAI-compatible endpoint) first, K2 as fallback; see flag 26.
    llm_provider: Literal["gemini", "k2"] = "gemini"
    gemini_api_key: SecretStr | None = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    gemini_model: str = "gemini-2.5-flash"

    # K2 Horizon hosted API (OpenAI-compatible).
    k2_api_key: SecretStr | None = None
    k2_base_url: str = "https://api.ifm.ai/v1"
    k2_model: str = "IFM/K2-Horizon-375B-A23B"

    # Backup LLM and speech-to-text: Groq free tier (OpenAI-compatible).
    groq_api_key: SecretStr | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"

    database_url: str | None = None
    # Law-search embedder (flag 15): "cloudflare" = BGE-M3 on Workers AI (free tier);
    # "hash" = deterministic stand-in for tests and offline work. Ingest and API must match.
    embedder: Literal["hash", "cloudflare"] = "hash"
    cloudflare_account_id: str | None = None
    cloudflare_api_token: SecretStr | None = None
    # Comma-separated in env files (`a,b`); a JSON list also works.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    git_sha: str = "dev"
    # Test-only hooks such as TC-11's seeded bad citation (task 3.9). Never set in production.
    haqqi_test_hooks: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        text = value.strip()
        if text.startswith("["):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                # Some .env loaders (e.g. `uv run --env-file`) strip the inner quotes: [a, b]
                text = text[1:-1] if text.endswith("]") else text[1:]
        return [part.strip().strip("'\"") for part in text.split(",") if part.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
