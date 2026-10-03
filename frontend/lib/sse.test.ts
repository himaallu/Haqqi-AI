import { describe, expect, it } from "vitest";

import { parseFrames, readSSE, type SSEEvent } from "./sse";

function streamOf(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      chunks.forEach((c) => controller.enqueue(encoder.encode(c)));
      controller.close();
    },
  });
}

describe("parseFrames", () => {
  it("returns complete frames and keeps the unfinished tail", () => {
    const { events, rest } = parseFrames('event: retrieving\ndata: {}\n\nevent: done\ndata: {"a"');
    expect(events).toEqual([{ event: "retrieving", data: "{}" }]);
    expect(rest).toBe('event: done\ndata: {"a"');
  });

  it("joins multi-line data, ignores comments and accepts CRLF", () => {
    const { events } = parseFrames(": ping\r\n\r\nevent: x\r\ndata: a\r\ndata: b\r\n\r\n");
    expect(events).toEqual([{ event: "x", data: "a\nb" }]);
  });
});

describe("readSSE", () => {
  it("parses events split across chunks, including multi-byte characters", async () => {
    const got: SSEEvent[] = [];
    const body = 'event: analysing\ndata: {}\n\nevent: done\ndata: {"explanation":"आपका नतीजा"}\n\n';
    const chunks = [body.slice(0, 7), body.slice(7, 40), body.slice(40)];
    await readSSE(streamOf(chunks), (e) => got.push(e));
    expect(got.map((e) => e.event)).toEqual(["analysing", "done"]);
    expect(JSON.parse(got[1].data)).toEqual({ explanation: "आपका नतीजा" });
  });

  it("delivers a final frame that has no trailing blank line", async () => {
    const got: SSEEvent[] = [];
    await readSSE(streamOf(['event: error\ndata: {"detail":"busy"}']), (e) => got.push(e));
    expect(got).toEqual([{ event: "error", data: '{"detail":"busy"}' }]);
  });
});
