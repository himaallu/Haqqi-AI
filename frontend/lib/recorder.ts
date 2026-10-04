/** Recording the story in the browser (task 6.2). */

export const MAX_RECORDING_SECONDS = 120; // the backend caps uploads at 3 MB (haqqi/api/transcribe.py)

// Chrome and Android record WebM/Opus; iPhone Safari records MP4 (AAC). Both transcribe the same.
const PREFERRED = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];

/** The first format this browser can record, or "" to let it pick its default. */
export function pickMimeType(isTypeSupported: (type: string) => boolean): string {
  return PREFERRED.find((type) => isTypeSupported(type)) ?? "";
}

export function canRecord(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.MediaRecorder !== "undefined" &&
    Boolean(navigator.mediaDevices?.getUserMedia)
  );
}

/** 75 → "1:15" */
export function formatClock(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}
