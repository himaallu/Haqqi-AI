import { describe, expect, it } from "vitest";

import { PREPARED } from "./data";
import {
  citationLabel,
  display,
  isDanger,
  knownFromExtracted,
  matchPrepared,
  nextField,
  parseAmount,
  patchBody,
  shortRef,
} from "./logic";
import { strings } from "./strings";

describe("demo logic", () => {
  it("asks only for what the story didn't answer, in order", () => {
    const known = knownFromExtracted({ emirate: "abu_dhabi", termination: "employer", start_date: "2024-06-01", end_date: null });
    expect(nextField(known)).toBe("zone");
    expect(nextField({ ...known, zone: "mainland", worker_type: "private_sector" })).toBe("end_date");
  });

  it("skips the last day while the worker is still employed", () => {
    const known = { zone: "mainland", worker_type: "private_sector", emirate: "dubai", termination: "still_employed", start_date: "2024-01-01" };
    expect(nextField(known)).toBe("total_wage_aed");
    expect(nextField({ ...known, total_wage_aed: "3000", basic_wage_aed: "2000" })).toBeNull();
  });

  it("sends only answered fields, never nulls", () => {
    expect(patchBody({ zone: "mainland", emirate: "", end_date: "2026-01-01", termination: "still_employed" })).toEqual({
      zone: "mainland",
      termination: "still_employed",
    });
  });

  it("matches a prepared answer by keywords in any of the three languages", () => {
    expect(matchPrepared("Can my company keep my passport?", PREPARED)?.reply.citations[0].chunk_id).toBe("fdl33-2021:art13:cl2");
    expect(matchPrepared("کیا کمپنی میرا پاسپورٹ رکھ سکتی ہے؟", PREPARED)?.reply.headline).toContain("passport");
    expect(matchPrepared("what is the weather", PREPARED)).toBeNull();
  });

  it("spots danger words", () => {
    expect(isDanger("My supervisor beats us and locked us in the room.")).toBe(true);
    expect(isDanger("My salary is late")).toBe(false);
  });

  it("reads amounts typed on Arabic, Urdu and Hindi keyboards", () => {
    expect(parseAmount("٣٠٠٠")).toBe("3000");
    expect(parseAmount("۲,۰۰۰ درہم")).toBe("2000");
    expect(parseAmount("३०००")).toBe("3000");
    expect(parseAmount("zero")).toBeNull();
  });

  it("labels articles", () => {
    expect(shortRef("Art. 27(1), Cabinet Resolution No. 1 of 2022")).toBe("CR Art. 27(1)");
    expect(citationLabel({ chunk_id: "fdl33-2021:art53", law_id: "fdl33-2021", article_no: 53, clause_no: null, quote: "" })).toBe("Art. 53");
  });

  it("shows facts in plain words", () => {
    const s = strings("en");
    expect(display("zone", "mainland", s, "en")).toBe("No, not in a free zone");
    expect(display("total_wage_aed", "3000", s, "en")).toBe("AED 3,000");
    expect(display("start_date", "2024-06-01", s, "en")).toBe("June 1, 2024");
  });
});
