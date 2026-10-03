/** Server-Sent Events over fetch: the analyse endpoint is a POST, which EventSource cannot send. */

export type SSEEvent = { event: string; data: string };

/** Splits complete frames off `buffer`; returns them and the unfinished remainder. */
export function parseFrames(buffer: string): { events: SSEEvent[]; rest: string } {
  const normalised = buffer.replace(/\r\n?/g, "\n");
  const parts = normalised.split("\n\n");
  const rest = parts.pop() ?? "";
  const events: SSEEvent[] = [];
  for (const frame of parts) {
    let event = "message";
    const data: string[] = [];
    for (const line of frame.split("\n")) {
      if (!line || line.startsWith(":")) continue;
      const colon = line.indexOf(":");
      const field = colon === -1 ? line : line.slice(0, colon);
      const value = colon === -1 ? "" : line.slice(colon + 1).replace(/^ /, "");
      if (field === "event") event = value;
      else if (field === "data") data.push(value);
    }
    if (data.length) events.push({ event, data: data.join("\n") });
  }
  return { events, rest };
}

export async function readSSE(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: SSEEvent) => void,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
    const parsed = parseFrames(done ? `${buffer}\n\n` : buffer);
    parsed.events.forEach(onEvent);
    buffer = parsed.rest;
    if (done) return;
  }
}
