import { describe, expect, it } from "vitest";

import { formatAed } from "./money";

describe("formatAed", () => {
  it("groups thousands and keeps the calculator's digits", () => {
    expect(formatAed("6229.59")).toBe("AED 6,229.59");
    expect(formatAed("18381.37")).toBe("AED 18,381.37");
    expect(formatAed("1234567.1")).toBe("AED 1,234,567.10");
    expect(formatAed("0")).toBe("AED 0.00");
    expect(formatAed("950.00")).toBe("AED 950.00");
  });
});
