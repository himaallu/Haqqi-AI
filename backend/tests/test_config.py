from pathlib import Path

import pytest

from haqqi.config import Settings

ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"


def test_settings_load_from_env_example(monkeypatch: pytest.MonkeyPatch) -> None:
    for line in ENV_EXAMPLE.read_text().splitlines():
        if line and not line.startswith("#"):
            key, _, value = line.partition("=")
            monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)

    assert settings.k2_base_url == "https://api.ifm.ai/v1"
    assert settings.cors_origins == ["http://localhost:3000"]
    assert settings.database_url is not None


def test_every_setting_is_documented_in_env_example() -> None:
    documented = {
        line.partition("=")[0].lower()
        for line in ENV_EXAMPLE.read_text().splitlines()
        if line and not line.startswith("#")
    }
    assert set(Settings.model_fields) - {"git_sha"} <= documented


def test_api_keys_are_hidden_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("K2_API_KEY", "super-secret-value")
    settings = Settings(_env_file=None)

    assert "super-secret-value" not in repr(settings)
