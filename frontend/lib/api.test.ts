import { describe, expect, it, vi } from "vitest";

import { apiUrl, fetchHealth } from "./api";

describe("apiUrl", () => {
  it("joins base and path with exactly one slash", () => {
    expect(apiUrl("/healthz", "https://api.example.com/")).toBe("https://api.example.com/healthz");
    expect(apiUrl("healthz", "https://api.example.com")).toBe("https://api.example.com/healthz");
  });
});

describe("fetchHealth", () => {
  it("returns the parsed health payload", async () => {
    const body = { status: "ok", db: "down", version: "dev" };
    const fakeFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status: 200 }));

    await expect(fetchHealth(fakeFetch)).resolves.toEqual(body);
  });

  it("throws on a non-2xx response", async () => {
    const fakeFetch = vi.fn().mockResolvedValue(new Response("nope", { status: 503 }));

    await expect(fetchHealth(fakeFetch)).rejects.toThrow("503");
  });
});
