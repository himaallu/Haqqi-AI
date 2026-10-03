import shutil
import subprocess
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


@pytest.mark.parametrize(
    "raw",
    [
        "https://a.example,https://b.example",
        "https://a.example, https://b.example",
        '["https://a.example", "https://b.example"]',
        "[https://a.example, https://b.example]",  # JSON after `uv run --env-file` strips quotes
    ],
)
def test_cors_origins_accepts_common_env_formats(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    monkeypatch.setenv("CORS_ORIGINS", raw)

    settings = Settings(_env_file=None)

    assert settings.cors_origins == ["https://a.example", "https://b.example"]


def test_env_example_loads_through_dotenv_file(monkeypatch: pytest.MonkeyPatch) -> None:
    # Read the file the way real tools do (dotenv parsing), not line by line.
    for key in ("CORS_ORIGINS", "DATABASE_URL", "K2_API_KEY", "GROQ_API_KEY"):
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=ENV_EXAMPLE)

    assert settings.cors_origins == ["http://localhost:3000"]


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv not installed")
def test_settings_load_under_uv_env_file_with_json_cors(tmp_path: Path) -> None:
    # Regression: `uv run --env-file .env` strips the quotes in a JSON list and used to crash.
    env_file = tmp_path / ".env"
    env_file.write_text('CORS_ORIGINS=["http://localhost:3000"]\n')

    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "uv",
            "run",
            "--env-file",
            str(env_file),
            "python",
            "-c",
            "from haqqi.config import Settings; print(Settings(_env_file=None).cors_origins)",
        ],
        cwd=ENV_EXAMPLE.parent / "backend",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "['http://localhost:3000']"


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


def test_health_version_comes_from_render_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc1234")
    assert Settings(_env_file=None).git_sha == "abc1234"
