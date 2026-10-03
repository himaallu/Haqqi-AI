import { describe, expect, it } from "vitest";

import type { Violation } from "./types";
import { groupViolations } from "./violations";

const v = (issue: string, chunk_id: string): Violation => ({
  issue,
  confidence: "high",
  article: { chunk_id, law_id: "fdl33-2021", article_no: 43, clause_no: 1, quote: "" },
});

describe("groupViolations", () => {
  it("puts every clause of one finding on one card, without repeats", () => {
    const found = groupViolations([
      v("No notice", "fdl33-2021:art43:cl1"),
      v("No notice", "fdl33-2021:art43:cl3"),
      v("Unlawful termination", "fdl33-2021:art42:cl3"),
      v("Unlawful termination", "fdl33-2021:art43:cl1"),
      v("No notice", "fdl33-2021:art43:cl1"),
    ]);
    expect(found.map((f) => [f.issue, f.citations.map((c) => c.chunk_id)])).toEqual([
      ["No notice", ["fdl33-2021:art43:cl1", "fdl33-2021:art43:cl3"]],
      ["Unlawful termination", ["fdl33-2021:art42:cl3", "fdl33-2021:art43:cl1"]],
    ]);
  });
});
