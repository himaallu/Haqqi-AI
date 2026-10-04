"""Speech to text for the story (task 6.1, F1 voice): Whisper large-v3-turbo on Workers AI.

Free tier on the Cloudflare account we already use for embeddings; Cloudflare does not train on
or otherwise reuse request content (docs: workers-ai/platform/data-usage). Audio and transcripts
are never stored or logged.
"""

import base64
from dataclasses import dataclass
from typing import Protocol

import httpx

from haqqi.config import Settings


class SpeechError(Exception):
    """The speech service failed. The worker can still type the story."""


@dataclass(frozen=True)
class Transcript:
    text: str
    detected_language: str | None
    duration_s: float | None


class Transcriber(Protocol):
    def transcribe(self, audio: bytes, language: str | None) -> Transcript: ...


class CloudflareWhisper:
    MODEL = "@cf/openai/whisper-large-v3-turbo"

    def __init__(self, account_id: str, api_token: str, client: httpx.Client | None = None) -> None:
        self._url = (
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{self.MODEL}"
        )
        self._headers = {"Authorization": f"Bearer {api_token}"}
        self._client = client or httpx.Client(timeout=60.0)

    def transcribe(self, audio: bytes, language: str | None) -> Transcript:
        # The worker's chosen language is a hint: spoken Hindi and Urdu sound alike, and the
        # hint decides the script (Devanagari or Urdu).
        body: dict[str, object] = {"audio": base64.b64encode(audio).decode("ascii")}
        if language:
            body["language"] = language
        try:
            resp = self._client.post(self._url, headers=self._headers, json=body)
        except httpx.HTTPError as exc:
            raise SpeechError(f"speech service unreachable ({type(exc).__name__})") from None
        try:
            data = resp.json()
        except ValueError:
            data = {}
        if resp.status_code != 200 or not data.get("success"):
            raise SpeechError(f"speech service failed (HTTP {resp.status_code})")
        result = data.get("result") or {}
        info = result.get("transcription_info") or {}
        return Transcript(
            text=str(result.get("text") or "").strip(),
            detected_language=info.get("language"),
            duration_s=info.get("duration"),
        )


def get_transcriber(settings: Settings) -> Transcriber | None:
    if not (settings.cloudflare_account_id and settings.cloudflare_api_token):
        return None
    return CloudflareWhisper(
        settings.cloudflare_account_id, settings.cloudflare_api_token.get_secret_value()
    )
