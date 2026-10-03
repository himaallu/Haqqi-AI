import { describe, expect, it } from "vitest";

import { articleRef, lawName } from "./citation";

const cite = (law_id: string, article_no: number, clause_no: number | null) => ({
  chunk_id: "x", law_id, article_no, clause_no, quote: "",
});

describe("citation labels", () => {
  it("formats article and clause", () => {
    expect(articleRef(cite("fdl33-2021", 51, 2))).toBe("51(2)");
    expect(articleRef(cite("fdl33-2021", 53, null))).toBe("53");
  });

  it("names the law, falling back to its id", () => {
    expect(lawName(cite("fdl33-2021", 51, 2))).toBe("Federal Decree-Law 33/2021");
    expect(lawName(cite("cr1-2022", 30, 1))).toBe("Cabinet Resolution 1/2022");
    expect(lawName(cite("other", 1, null))).toBe("other");
  });
});
