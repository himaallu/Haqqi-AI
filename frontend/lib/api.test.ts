import { describe, expect, it, vi } from "vitest";

import {
  analyzeCase,
  ApiError,
  apiUrl,
  confirmCase,
  createCase,
  downloadComplaint,
  fetchHealth,
  getCase,
  transcribeAudio,
} from "./api";

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

describe("case calls", () => {
  it("POSTs the story as JSON and returns the case", async () => {
    const view = { id: "abc", status: "ready" };
    const fakeFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(view), { status: 201 }));

    await expect(createCase({ language: "hi", story: "salary unpaid" }, fakeFetch)).resolves.toEqual(view);
    const [url, init] = fakeFetch.mock.calls[0];
    expect(url).toMatch(/\/v1\/cases$/);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ language: "hi", story: "salary unpaid" });
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
  });

  it("raises ApiError with FastAPI's detail on 422", async () => {
    const detail = [{ loc: ["total_wage_aed"], msg: "Input should be greater than 0" }];
    const fakeFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail }), { status: 422 }));

    const err = await confirmCase("abc", { total_wage_aed: "0" }, fakeFetch).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).status).toBe(422);
    expect((err as ApiError).detail).toEqual(detail);
  });

  it("GETs a case by id", async () => {
    const fakeFetch = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    await getCase("a/b", fakeFetch);
    expect(fakeFetch.mock.calls[0][0]).toMatch(/\/v1\/cases\/a%2Fb$/);
  });

  it("streams analysis events", async () => {
    const body = 'event: retrieving\ndata: {}\n\nevent: done\ndata: {"in_scope":true}\n\n';
    const fakeFetch = vi.fn().mockResolvedValue(new Response(body, { status: 200 }));
    const names: string[] = [];

    await analyzeCase("abc", (e) => names.push(e.event), undefined, fakeFetch);
    expect(names).toEqual(["retrieving", "done"]);
    expect(fakeFetch.mock.calls[0][1].method).toBe("POST");
  });

  it("raises ApiError when analysis is refused", async () => {
    const fakeFetch = vi.fn().mockResolvedValue(new Response('{"detail":"confirm first"}', { status: 409 }));
    await expect(analyzeCase("abc", () => {}, undefined, fakeFetch)).rejects.toMatchObject({ status: 409 });
  });
});

describe("downloadComplaint", () => {
  it("POSTs only the filled identity fields and returns the PDF", async () => {
    const fakeFetch = vi.fn().mockResolvedValue(
      new Response(new Blob(["%PDF-1.7"], { type: "application/pdf" }), { status: 200 }),
    );

    const pdf = await downloadComplaint("a/b", { name: "  Ramesh ", labour_card: " ", employer: "" }, fakeFetch);

    expect(await pdf.text()).toBe("%PDF-1.7");
    const [url, init] = fakeFetch.mock.calls[0];
    expect(url).toMatch(/\/v1\/cases\/a%2Fb\/complaint$/);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ name: "Ramesh" });
  });

  it("raises ApiError when the case has no complaint yet", async () => {
    const fakeFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "x" }), { status: 409 }));
    const err = await downloadComplaint("abc", {}, fakeFetch).catch((e: unknown) => e);
    expect((err as ApiError).status).toBe(409);
  });
});

describe("transcribeAudio", () => {
  it("uploads the recording as multipart with the language, without a JSON content type", async () => {
    const body = { text: "पिछले तीन महीने", detected_language: "hi" };
    const fakeFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status: 200 }));

    await expect(transcribeAudio(new Blob(["x"], { type: "audio/mp4" }), "hi", fakeFetch)).resolves.toEqual(body);

    const [url, init] = fakeFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/v1\/transcribe$/);
    expect(init.headers).toBeUndefined();
    const form = init.body as FormData;
    expect(form.get("language")).toBe("hi");
    expect((form.get("audio") as File).name).toBe("recording.m4a");
  });

  it("throws ApiError when the speech service is down", async () => {
    const fakeFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "x" }), { status: 503 }));
    await expect(transcribeAudio(new Blob(["x"]), "en", fakeFetch)).rejects.toBeInstanceOf(ApiError);
  });
});
