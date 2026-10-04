"""Log redaction (task 8.3): masks, hidden exception messages, length cap."""

import io
import logging

from haqqi.logs import MAX_CHARS, RedactingFilter, redact

STORY = "My boss Ramesh Kumar did not pay me. Call me on +971 50 123 4567."


def capture() -> tuple[logging.Logger, io.StringIO]:
    out = io.StringIO()
    handler = logging.StreamHandler(out)
    handler.addFilter(RedactingFilter())
    logger = logging.getLogger("test.redaction")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    return logger, out


def test_masks_phones_emails_and_id_numbers() -> None:
    text = redact(
        "+971 50 123 4567, 0501234567, worker@example.com, 784-1990-1234567-1, "
        "784199012345671, passport N1234567"
    )
    assert text == "[number], [number], [email], [emirates-id], [emirates-id], passport [id]"


def test_keeps_dates_and_amounts() -> None:
    line = "total 6229.59 AED 16,056.85 on 2026-09-20, 3 months, 21 days"
    assert redact(line) == line


def test_masks_case_ids_in_paths() -> None:
    line = '"POST /v1/cases/3f2b9c1e-0000-4000-8000-000000000001/analyze HTTP/1.1" 200'
    assert redact(line) == '"POST /v1/cases/[case-id]/analyze HTTP/1.1" 200'


def test_caps_long_lines() -> None:
    assert len(redact("x" * 5000)) < MAX_CHARS + 20


def test_log_arguments_are_redacted() -> None:
    logger, out = capture()
    logger.warning("reply from %s", "worker@example.com")
    assert "worker@example.com" not in out.getvalue()
    assert "[email]" in out.getvalue()


def test_exception_messages_are_hidden_but_type_and_frames_kept() -> None:
    logger, out = capture()
    try:
        raise ValueError(STORY)
    except ValueError:
        logger.exception("analysis crashed")
    logged = out.getvalue()
    assert "Ramesh" not in logged and "123 4567" not in logged
    assert "analysis crashed" in logged
    assert "ValueError" in logged and "test_redaction.py" in logged
