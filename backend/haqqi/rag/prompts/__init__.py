"""System prompts for the agents (task 3.6). Material changes from n8n are listed in CHANGES.md."""

from functools import cache
from pathlib import Path
from string import Template

PROMPT_DIR = Path(__file__).resolve().parent


@cache
def _read(name: str) -> str:
    return (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")


def system_prompt(name: str, **values: str) -> str:
    """The system prompt `name` (intake, analyst, critic, revision, writer) with $values filled."""
    if name == "revision":
        return _read("analyst") + _read("revision")
    return Template(_read(name)).substitute(values)
