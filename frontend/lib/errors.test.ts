import { describe, expect, it } from "vitest";

import { ApiError } from "./api";
import { errorMessageKey } from "./errors";

describe("errorMessageKey", () => {
  it.each([
    [new ApiError(503, "busy"), "error.busy"],
    [new ApiError(429, null), "error.busy"],
    [new ApiError(502, "bad"), "error.invalid"],
    [new ApiError(404, "case not found"), "error.notFound"],
    [new ApiError(500, null), "error.generic"],
    [new TypeError("Failed to fetch"), "error.network"],
    [new Error("?"), "error.generic"],
  ])("%o → %s", (err, key) => {
    expect(errorMessageKey(err)).toBe(key);
  });
});
