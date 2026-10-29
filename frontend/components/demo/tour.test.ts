import { describe, expect, it } from "vitest";

import { stepDone, TOUR, tourText } from "./tour";

const step = (id: string) => {
  const found = TOUR.find((s) => s.id === id);
  if (!found) throw new Error(id);
  return found;
};

describe("guided tour", () => {
  it("starts with a welcome and ends with a wrap-up, both moved on by Next", () => {
    expect(TOUR[0].id).toBe("welcome");
    expect(TOUR[TOUR.length - 1].id).toBe("end");
    expect(TOUR[0].done).toBeUndefined();
    expect(stepDone(TOUR[0], [{ id: 1, t: "answer" }], 0)).toBe(false);
  });

  it("moves on only for messages added after the step started", () => {
    const ask = step("ask");
    expect(stepDone(ask, [{ id: 3, t: "answer" }], 5)).toBe(false);
    expect(stepDone(ask, [{ id: 6, t: "answer" }], 5)).toBe(true);
    expect(stepDone(ask, [{ id: 6, t: "notice" }], 5)).toBe(true); // an "unsure" reply still moves on
  });

  it("waits for the contract check to finish, not just start", () => {
    const scan = step("scan");
    expect(stepDone(scan, [{ id: 9, t: "contract", stage: "scanning" }], 8)).toBe(false);
    expect(stepDone(scan, [{ id: 9, t: "contract", stage: "done" }], 8)).toBe(true);
  });

  it("walks the case: facts card, then the result", () => {
    expect(stepDone(step("case"), [{ id: 20, t: "me" }, { id: 21, t: "facts" }], 19)).toBe(true);
    expect(stepDone(step("facts"), [{ id: 22, t: "progress" }], 22)).toBe(false);
    expect(stepDone(step("facts"), [{ id: 23, t: "result" }], 22)).toBe(true);
  });

  it("has English and Arabic text for every step, Arabic only for ar", () => {
    for (const s of TOUR) {
      expect(s.text.en.title && s.text.en.body).toBeTruthy();
      expect(s.text.ar.title && s.text.ar.body).toBeTruthy();
      expect(Boolean(s.text.en.wait)).toBe(Boolean(s.text.ar.wait));
    }
    expect(tourText(TOUR[0], "ar")).toBe(TOUR[0].text.ar);
    expect(tourText(TOUR[0], "hi")).toBe(TOUR[0].text.en);
  });
});
