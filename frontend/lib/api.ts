import { readSSE, type SSEEvent } from "./sse";
import type { CaseView, Language, WorkerType, Zone } from "./types";

export type Health = {
  status: "ok";
  db: "ok" | "down";
  version: string;
};

/** Base URL of the backend. The browser calls it directly (not via a Next.js route) so long SSE streams aren't cut off. */
export function apiUrl(path: string, base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"): string {
  return `${base.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;
}

/** A non-2xx reply. `detail` is FastAPI's `detail` (a string, or Pydantic errors for a 422). */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: unknown,
  ) {
    super(`API returned ${status}`);
  }
}

async function request<T>(fetchFn: typeof fetch, path: string, init: RequestInit = {}): Promise<T> {
  const resp = await fetchFn(apiUrl(path), {
    cache: "no-store",
    ...init,
    headers: init.body ? { "Content-Type": "application/json" } : undefined,
  });
  if (!resp.ok) throw new ApiError(resp.status, await errorDetail(resp));
  return (await resp.json()) as T;
}

async function errorDetail(resp: Response): Promise<unknown> {
  try {
    return ((await resp.json()) as { detail?: unknown }).detail ?? null;
  } catch {
    return null;
  }
}

export async function fetchHealth(fetchFn: typeof fetch = fetch): Promise<Health> {
  const resp = await fetchFn(apiUrl("/healthz"), { cache: "no-store" });
  if (!resp.ok) throw new Error(`healthz returned ${resp.status}`);
  return (await resp.json()) as Health;
}

export type CreateCase = { language: Language; story: string; zone?: Zone; worker_type?: WorkerType };

export function createCase(body: CreateCase, fetchFn: typeof fetch = fetch): Promise<CaseView> {
  return request(fetchFn, "/v1/cases", { method: "POST", body: JSON.stringify(body) });
}

export function getCase(id: string, fetchFn: typeof fetch = fetch): Promise<CaseView> {
  return request(fetchFn, `/v1/cases/${encodeURIComponent(id)}`);
}

export function confirmCase(
  id: string,
  edits: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<CaseView> {
  return request(fetchFn, `/v1/cases/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(edits),
  });
}

/** Starts the analysis and calls `onEvent` for each stage, then `done` (or `error`). */
export async function analyzeCase(
  id: string,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal,
  fetchFn: typeof fetch = fetch,
): Promise<void> {
  const resp = await fetchFn(apiUrl(`/v1/cases/${encodeURIComponent(id)}/analyze`), {
    method: "POST",
    cache: "no-store",
    signal,
  });
  if (!resp.ok || !resp.body) throw new ApiError(resp.status, await errorDetail(resp));
  await readSSE(resp.body, onEvent);
}

/** Printed into the complaint PDF only; the backend never stores or logs them (flag 8). */
export type ComplaintIdentity = { name?: string; labour_card?: string; employer?: string };

/** The complaint letter as a PDF (task 5.5). Empty identity fields are left as lines to fill in by hand. */
export async function downloadComplaint(
  id: string,
  identity: ComplaintIdentity,
  fetchFn: typeof fetch = fetch,
): Promise<Blob> {
  const body = Object.fromEntries(
    Object.entries(identity)
      .map(([key, value]) => [key, value?.trim()])
      .filter(([, value]) => value),
  );
  const resp = await fetchFn(apiUrl(`/v1/cases/${encodeURIComponent(id)}/complaint`), {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new ApiError(resp.status, await errorDetail(resp));
  return resp.blob();
}

export type Transcription = { text: string; detected_language: string | null };

/** Voice → text for the story box (task 6.1). The recording is sent once and never stored. */
export async function transcribeAudio(
  audio: Blob,
  language: Language,
  fetchFn: typeof fetch = fetch,
): Promise<Transcription> {
  const form = new FormData();
  form.append("audio", audio, `recording.${audioExtension(audio.type)}`);
  form.append("language", language);
  // No Content-Type header: the browser sets the multipart boundary itself.
  const resp = await fetchFn(apiUrl("/v1/transcribe"), { method: "POST", cache: "no-store", body: form });
  if (!resp.ok) throw new ApiError(resp.status, await errorDetail(resp));
  return (await resp.json()) as Transcription;
}

function audioExtension(type: string): string {
  if (type.includes("mp4") || type.includes("aac")) return "m4a";
  if (type.includes("ogg")) return "ogg";
  return "webm";
}
