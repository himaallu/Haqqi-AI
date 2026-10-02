"""System prompts for the agents (task 3.6). Material changes from n8n are listed in CHANGES.md."""

from functools import cache
from pathlib import Path
from string import Template

PROMPT_DIR = Path(__file__).resolve().parent
TEMPLATE_AR_FILE = PROMPT_DIR.parents[1] / "pdf" / "template_ar.txt"


@cache
def _read(name: str) -> str:
    return (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")


def system_prompt(name: str, **values: str) -> str:
    """The system prompt `name` (intake, analyst, critic, revision, writer) with $values filled."""
    if name == "revision":
        return _read("analyst") + _read("revision")
    return Template(_read(name)).substitute(values)


@cache
def template_ar() -> str:
    return TEMPLATE_AR_FILE.read_text(encoding="utf-8")
