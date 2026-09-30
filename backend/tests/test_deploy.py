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


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv not installed")
def test_requirements_resolve_alongside_hf_space_gradio(tmp_path: Path) -> None:
    # A Gradio-SDK Space pip-installs requirements.txt together with
    # gradio[oauth,mcp]==<sdk_version>.
    # Resolving the same set here catches pin clashes (e.g. pydantic) before the Space build fails.
    readme = (BACKEND / "README.md").read_text()
    sdk_version = next(
        line.split(":", 1)[1].strip()
        for line in readme.splitlines()
        if line.startswith("sdk_version:")
    )
    hf_extras = tmp_path / "hf-space.in"
    hf_extras.write_text(f"gradio[oauth,mcp]=={sdk_version}\nuvicorn>=0.14.0\nwebsockets>=10.4\n")

    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "uv",
            "pip",
            "compile",
            "--python-version",
            "3.12",
            "--quiet",
            "-o",
            "/dev/null",
            str(BACKEND / "requirements.txt"),
            str(hf_extras),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"HF Space install would fail:\n{result.stderr}"


def test_space_entry_point_exposes_the_api() -> None:
    import app  # backend/app.py, the Hugging Face Spaces entry point

    assert any(getattr(route, "path", None) == "/healthz" for route in app.app.routes)
