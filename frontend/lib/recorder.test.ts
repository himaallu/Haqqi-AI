import { describe, expect, it } from "vitest";

import { formatClock, pickMimeType } from "./recorder";

describe("recorder", () => {
  it("prefers WebM/Opus, then MP4 for iPhone Safari, else the browser default", () => {
    expect(pickMimeType(() => true)).toBe("audio/webm;codecs=opus");
    expect(pickMimeType((t) => t === "audio/mp4")).toBe("audio/mp4");
    expect(pickMimeType(() => false)).toBe("");
  });

  it("formats the timer", () => {
    expect(formatClock(0)).toBe("0:00");
    expect(formatClock(75.9)).toBe("1:15");
    expect(formatClock(120)).toBe("2:00");
  });
});
