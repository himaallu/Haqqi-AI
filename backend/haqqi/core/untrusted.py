"""The worker's story is data, never instructions (CLAUDE.md). Task 3.4.

Everything the worker typed reaches a prompt only through `wrap_worker_data`, which fences it
between fixed delimiters and removes any copy of those delimiters from inside the text, so
the story cannot close the fence early and speak as the system.
"""

import re

OPEN = "<<<WORKER_DATA>>>"
CLOSE = "<<<END_WORKER_DATA>>>"

_DELIMITER = re.compile(r"<<<\s*(?:END_)?WORKER_DATA\s*>>>", re.IGNORECASE)
# Control characters other than tab and newline (e.g. NUL, escape codes, bidi overrides).
_CONTROL = re.compile("[\x00-\x08\x0b-\x1f\x7f‪-‮⁦-⁩]")


def clean_text(text: str) -> str:
    return _CONTROL.sub("", text.replace("\r\n", "\n")).strip()


def wrap_worker_data(text: str) -> str:
    """Fence untrusted worker text for a prompt."""
    body = _DELIMITER.sub("", clean_text(text))
    return f"{OPEN}\n{body}\n{CLOSE}"
