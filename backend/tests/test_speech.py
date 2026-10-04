import base64
import json
from pathlib import Path

import httpx
import pytest

from haqqi.config import Settings
from haqqi.speech import CloudflareWhisper, SpeechError, get_transcriber

FIXTURE = Path(__file__).parent / "fixtures" / "hi.webm"


def whisper_with(response: httpx.Response, seen: list[dict[str, object]]) -> CloudflareWhisper:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return response

    return CloudflareWhisper("acct", "token", httpx.Client(transport=httpx.MockTransport(handler)))


def test_sends_base64_audio_with_the_language_hint_and_reads_the_result() -> None:
    seen: list[dict[str, object]] = []
    ok = httpx.Response(
        200,
        json={
            "success": True,
            "result": {
                "text": " پچھلے تین مہینے سے ",
                "transcription_info": {"language": "ur", "duration": 4.6},
            },
        },
    )
    out = whisper_with(ok, seen).transcribe(b"\x1a\x45\xdf\xa3", "ur")

    assert out.text == "پچھلے تین مہینے سے"
    assert out.detected_language == "ur" and out.duration_s == 4.6
    assert seen == [{"audio": base64.b64encode(b"\x1a\x45\xdf\xa3").decode(), "language": "ur"}]


def test_no_hint_means_whisper_detects_the_language() -> None:
    seen: list[dict[str, object]] = []
    ok = httpx.Response(200, json={"success": True, "result": {"text": "hi"}})
    whisper_with(ok, seen).transcribe(b"x", None)
    assert "language" not in seen[0]


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500, json={"success": False, "errors": [{"message": "boom"}]}),
        httpx.Response(200, json={"success": False}),
        httpx.Response(502, text="bad gateway"),
    ],
)
def test_service_failures_raise_speech_error(response: httpx.Response) -> None:
    with pytest.raises(SpeechError):
        whisper_with(response, []).transcribe(b"x", "hi")


def test_no_cloudflare_credentials_means_no_transcriber(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    assert get_transcriber(Settings(_env_file=None)) is None


@pytest.mark.live
def test_live_hindi_recording_is_transcribed() -> None:
    settings = Settings()
    transcriber = get_transcriber(settings)
    if transcriber is None:
        pytest.skip("CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN not set")
    out = transcriber.transcribe(FIXTURE.read_bytes(), "hi")
    assert out.detected_language == "hi"
    assert "महीने" in out.text and "काम" in out.text
