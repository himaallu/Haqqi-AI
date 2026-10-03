import { ApiError } from "./api";
import type { MessageKey } from "./i18n/translate";

/** A message in the worker's language for a failed call; the backend's own text is English. */
export function errorMessageKey(err: unknown): MessageKey {
  if (err instanceof ApiError) {
    if (err.status === 503 || err.status === 429) return "error.busy";
    if (err.status === 502) return "error.invalid";
    if (err.status === 404) return "error.notFound";
    return "error.generic";
  }
  if (err instanceof TypeError) return "error.network"; // fetch() rejects with TypeError when offline
  return "error.generic";
}
