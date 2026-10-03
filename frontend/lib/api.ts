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
