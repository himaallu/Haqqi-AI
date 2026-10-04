"""Log setup and redaction (task 8.3).

Our own log lines carry no worker content (stage names, timings, error types). This filter is the
safety net for everything else that reaches a log handler, ours or uvicorn's:
- exception messages are dropped (they can quote the input, e.g. a validation error showing the
  story); only the exception type and the stack frames are kept;
- case ids, phone numbers, emails, Emirates ID and passport-like numbers are masked;
- every line is capped at MAX_CHARS.
"""

import logging
import re
import traceback

MAX_CHARS = 600

PATTERNS = [
    # Case ids: with no accounts, the id is the only key to a worker's case (PRD privacy).
    (
        re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I),
        "[case-id]",
    ),
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[email]"),
    # Emirates ID: 784-YYYY-NNNNNNN-N, with or without separators.
    (re.compile(r"\b784[-\s]?\d{4}[-\s]?\d{7}[-\s]?\d\b"), "[emirates-id]"),
    # Passport-like: one or two letters then 6–9 digits.
    (re.compile(r"\b[A-Za-z]{1,2}\d{6,9}\b"), "[id]"),
    # Phone numbers and other long numbers (labour card, IBAN digits): 9+ digits, optionally
    # with +, spaces or dashes between groups. Dates (8 digits) and amounts are left alone.
    (re.compile(r"\+?\d(?:[\s-]?\d){8,}"), "[number]"),
]


def redact(text: str) -> str:
    for pattern, mask in PATTERNS:
        text = pattern.sub(mask, text)
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + " …[truncated]"
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = None
        if record.exc_info and record.exc_info[0] is not None:
            exc_type, _, tb = record.exc_info
            frames = "".join(traceback.format_tb(tb))
            # The message is dropped on purpose: it can quote the worker's input.
            record.exc_text = f"Traceback (message hidden):\n{frames}{exc_type.__name__}"
            record.exc_info = None
        record.stack_info = None
        return True


def configure_logging(level: int = logging.INFO) -> None:
    """Log to stderr through the redacting filter, and add the filter to uvicorn's handlers."""
    root = logging.getLogger()
    if not any(isinstance(f, RedactingFilter) for h in root.handlers for f in h.filters):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        root.addHandler(handler)
    root.setLevel(level)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # one line per request is noise
    for name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
        for h in logging.getLogger(name).handlers:
            if not any(isinstance(f, RedactingFilter) for f in h.filters):
                h.addFilter(RedactingFilter())
