export type Health = {
  status: "ok";
  db: "ok" | "down";
  version: string;
};

/** Base URL of the backend. The browser calls it directly (not via a Next.js route) so long SSE streams aren't cut off. */
export function apiUrl(path: string, base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"): string {
  return `${base.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;
}

export async function fetchHealth(fetchFn: typeof fetch = fetch): Promise<Health> {
  const resp = await fetchFn(apiUrl("/healthz"), { cache: "no-store" });
  if (!resp.ok) throw new Error(`healthz returned ${resp.status}`);
  return (await resp.json()) as Health;
}
