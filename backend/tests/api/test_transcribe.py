"""POST /v1/transcribe with a fake speech service (no network, no database)."""

from pathlib import Path

from fastapi.testclient import TestClient

from haqqi.api import transcribe as api
from haqqi.api.main import create_app
from haqqi.speech import SpeechError, Transcript

FIXTURE = Path(__file__).parents[1] / "fixtures" / "hi.webm"


class FakeTranscriber:
    def __init__(self, fail: bool = False) -> None:
        self.calls: list[tuple[int, str | None]] = []
        self.fail = fail

    def transcribe(self, audio: bytes, language: str | None) -> Transcript:
        self.calls.append((len(audio), language))
        if self.fail:
            raise SpeechError("speech service failed (HTTP 500)")
        return Transcript(text="पिछले तीन महीने से", detected_language="hi", duration_s=4.6)


def client_with(transcriber: object) -> TestClient:
    app = create_app()
    app.dependency_overrides[api.get_transcriber_dep] = lambda: transcriber
    return TestClient(app)


def post(client: TestClient, data: bytes, mime: str = "audio/webm;codecs=opus", **form: str):  # type: ignore[no-untyped-def]
    return client.post("/v1/transcribe", files={"audio": ("rec", data, mime)}, data=form)


def test_returns_text_and_language_and_passes_the_hint() -> None:
    fake = FakeTranscriber()
    resp = post(client_with(fake), FIXTURE.read_bytes(), language="hi")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"text": "पिछले तीन महीने से", "detected_language": "hi"}
    assert fake.calls == [(FIXTURE.stat().st_size, "hi")]


def test_iphone_mp4_audio_is_accepted() -> None:
    m4a = b"\x00\x00\x00\x1cftypM4A "
    assert post(client_with(FakeTranscriber()), m4a, "audio/mp4").status_code == 200


def test_limits() -> None:
    client = client_with(FakeTranscriber())
    assert post(client, b"x" * (api.MAX_AUDIO_BYTES + 1)).status_code == 413
    assert post(client, b"", "audio/webm").status_code == 422
    assert post(client, b"not audio", "text/plain").status_code == 415
    assert post(client, b"x", language="fr").status_code == 422  # not a Haqqi language


def test_unavailable_service_says_type_instead() -> None:
    for transcriber in (None, FakeTranscriber(fail=True)):
        resp = post(client_with(transcriber), b"x")
        assert resp.status_code == 503
        assert "type your story" in resp.json()["detail"]
