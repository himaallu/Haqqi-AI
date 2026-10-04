"use client";

import { Loader2, Mic, Square } from "lucide-react";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";

import { Button } from "@/components/ui/button";
import { ApiError, transcribeAudio } from "@/lib/api";
import { errorMessageKey } from "@/lib/errors";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n/translate";
import { canRecord, formatClock, MAX_RECORDING_SECONDS, pickMimeType } from "@/lib/recorder";

const noSubscribe = () => () => {};

type State = { kind: "idle" } | { kind: "recording"; seconds: number } | { kind: "transcribing" };

/**
 * Step 2 by voice (tasks 6.1–6.2): record, send once to /v1/transcribe, append the text to the story.
 * The worker's language goes along as a hint (it decides Hindi vs Urdu script). Nothing is stored.
 */
export function VoiceInput({ onText, disabled }: { onText: (text: string) => void; disabled?: boolean }) {
  const { lang, t } = useI18n();
  const [state, setState] = useState<State>({ kind: "idle" });
  const [error, setError] = useState<MessageKey | null>(null);
  // Browser-only check; the server render assumes yes so the button doesn't flash in.
  const supported = useSyncExternalStore(noSubscribe, canRecord, () => true);
  const recorder = useRef<MediaRecorder | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => stopEverything(), []);

  function stopEverything() {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    const rec = recorder.current;
    if (rec && rec.state !== "inactive") rec.stop();
    rec?.stream.getTracks().forEach((track) => track.stop());
  }

  async function start() {
    setError(null);
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("story.micDenied");
      return;
    }
    const mimeType = pickMimeType((type) => MediaRecorder.isTypeSupported(type));
    const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    const chunks: Blob[] = [];
    rec.ondataavailable = (e) => {
      if (e.data.size) chunks.push(e.data);
    };
    rec.onstop = () => {
      stream.getTracks().forEach((track) => track.stop());
      void send(new Blob(chunks, { type: rec.mimeType || mimeType || "audio/webm" }));
    };
    recorder.current = rec;
    rec.start(1000);
    const started = Date.now();
    setState({ kind: "recording", seconds: 0 });
    timer.current = setInterval(() => {
      const seconds = (Date.now() - started) / 1000;
      if (seconds >= MAX_RECORDING_SECONDS) stop();
      else setState({ kind: "recording", seconds });
    }, 250);
  }

  function stop() {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    if (recorder.current?.state === "recording") {
      setState({ kind: "transcribing" });
      recorder.current.stop(); // onstop sends the audio
    }
  }

  async function send(audio: Blob) {
    if (!audio.size) {
      setError("story.micEmpty");
      setState({ kind: "idle" });
      return;
    }
    setState({ kind: "transcribing" });
    try {
      const { text } = await transcribeAudio(audio, lang);
      if (text.trim()) onText(text.trim());
      else setError("story.micEmpty");
    } catch (err) {
      setError(err instanceof ApiError && err.status === 503 ? "story.micUnavailable" : errorMessageKey(err));
    } finally {
      setState({ kind: "idle" });
    }
  }

  if (!supported) return <p className="text-sm text-muted-foreground">{t("story.micUnsupported")}</p>;

  return (
    <div className="flex flex-col gap-2" data-testid="voice">
      {state.kind === "recording" ? (
        <Button type="button" onClick={stop} data-testid="voice-stop">
          <Square aria-hidden className="size-4" />
          {t("story.micStop", { time: formatClock(state.seconds) })}
        </Button>
      ) : (
        <Button
          type="button"
          variant="outline"
          onClick={start}
          disabled={disabled || state.kind === "transcribing"}
          data-testid="voice-start"
        >
          {state.kind === "transcribing" ? (
            <Loader2 aria-hidden className="size-4 animate-spin" />
          ) : (
            <Mic aria-hidden className="size-4" />
          )}
          {state.kind === "transcribing" ? t("story.micTranscribing") : t("story.mic")}
        </Button>
      )}
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {t(error)}
        </p>
      )}
    </div>
  );
}
