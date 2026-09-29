import shutil
import subprocess
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv not installed")
def test_requirements_txt_matches_lockfile() -> None:
    exported = subprocess.run(
        ["uv", "export", "--no-dev", "--no-hashes", "--no-emit-project", "--frozen"],  # noqa: S607
        cwd=BACKEND,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    def pins(text: str) -> list[str]:
        return [line for line in text.splitlines() if line and not line.lstrip().startswith("#")]

    assert pins(exported) == pins((BACKEND / "requirements.txt").read_text()), (
        "requirements.txt is stale: run "
        "`uv export --no-dev --no-hashes --no-emit-project -o requirements.txt` in backend/"
    )


def test_space_entry_point_exposes_the_api() -> None:
    import app  # backend/app.py, the Hugging Face Spaces entry point

    assert any(getattr(route, "path", None) == "/healthz" for route in app.app.routes)
