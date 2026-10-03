import { describe, expect, it } from "vitest";

import { FIELDS, initialValues, normaliseNumber, serverErrors, toPatch, validate, type FormValues } from "./form";
import type { CaseView, ExtractedFacts } from "./types";

const EMPTY_EXTRACTED: ExtractedFacts = {
  language: null, issue_types: [], emirate: null, zone: null, free_zone_name: null, worker_type: null,
  contract_type: null, weekly_hours: null, start_date: null, end_date: null, basic_wage_aed: null,
  total_wage_aed: null, months_unpaid: null, deducted_amount_aed: null, deducted_monthly_aed: null,
  unused_leave_days: null, unpaid_absence_days: null, termination: null, notice_days_contract: null,
  notice_days_given: null, in_scope: null, scope_reason: "", missing_info: [], facts_summary_en: "",
};

function view(extracted: Partial<ExtractedFacts>, confirmed: Record<string, unknown> | null = null): CaseView {
  return {
    id: "x", status: "ready", extracted: { ...EMPTY_EXTRACTED, ...extracted }, missing: [], missing_fields: [],
    referral: null, referral_kind: null, confirmed, analysis: null,
  };
}

// TC-18: dates and wages come only from the story.
const TC18 = view({
  emirate: "dubai", zone: "mainland", worker_type: "private_sector", start_date: "2025-05-01",
  basic_wage_aed: "1600", total_wage_aed: "2200", termination: "employer", end_date: "2026-09-01",
});

function filled(overrides: Partial<FormValues> = {}): FormValues {
  return { ...initialValues(TC18).values, ...overrides };
}

describe("initialValues", () => {
  it("pre-fills from the intake and marks those fields for confirmation", () => {
    const { values, prefilled } = initialValues(TC18);
    expect(values.start_date).toBe("2025-05-01");
    expect(values.total_wage_aed).toBe("2200");
    expect(values.months_unpaid).toBe("");
    expect(prefilled.has("total_wage_aed")).toBe(true);
    expect(prefilled.has("months_unpaid")).toBe(false);
  });

  it("uses the confirmed facts after a reload, with nothing left to confirm", () => {
    const { values, prefilled } = initialValues(view({ total_wage_aed: "2200" }, { total_wage_aed: "2500", months_unpaid: 2 }));
    expect(values.total_wage_aed).toBe("2500");
    expect(values.months_unpaid).toBe("2");
    expect(prefilled.size).toBe(0);
  });
});

describe("validate", () => {
  it("passes a complete TC-18 form", () => {
    expect(validate(filled())).toEqual({ fields: {}, form: [] });
  });

  it("requires the core facts and the end date once the job has ended", () => {
    const { fields, form } = validate(initialValues(view({ termination: "resigned" })).values);
    expect(fields).toMatchObject({
      emirate: "confirm.required", zone: "confirm.required", worker_type: "confirm.required",
      start_date: "confirm.required", basic_wage_aed: "confirm.required", total_wage_aed: "confirm.required",
      end_date: "confirm.required",
    });
    expect(form).toEqual(["confirm.fixErrors"]);
  });

  it("does not ask for an end date while still employed", () => {
    expect(validate(filled({ termination: "still_employed", end_date: "" })).fields).toEqual({});
  });

  it("catches basic above total, end before start and bad numbers", () => {
    expect(validate(filled({ basic_wage_aed: "3000" })).form).toEqual(["confirm.basicAboveTotal"]);
    expect(validate(filled({ end_date: "2024-01-01" })).fields.end_date).toBe("confirm.endBeforeStart");
    expect(validate(filled({ months_unpaid: "two" })).fields.months_unpaid).toBe("confirm.invalid");
    expect(validate(filled({ total_wage_aed: "2,200.505" })).fields.total_wage_aed).toBe("confirm.invalid");
  });
});

describe("toPatch", () => {
  it("sends every field: numbers typed, money as decimal strings, defaults for empty answers", () => {
    const body = toPatch(filled({ months_unpaid: "٣", total_wage_aed: "2,200", unused_leave_days: "" }));
    expect(body).toMatchObject({
      emirate: "dubai", start_date: "2025-05-01", total_wage_aed: "2200", basic_wage_aed: "1600",
      months_unpaid: 3, contract_type: "full_time", notice_days_contract: 30, notice_days_given: 0,
      deducted_amount_aed: "0", deducted_monthly_aed: null, unused_leave_days: null, unpaid_absence_days: 0,
    });
    expect(Object.keys(body).sort()).toEqual(FIELDS.map((f) => f.name).sort());
  });

  it("nulls hidden fields so stale intake values don't survive", () => {
    const body = toPatch(filled({ termination: "still_employed", zone: "mainland", free_zone_name: "JAFZA" }));
    expect(body.end_date).toBeNull();
    expect(body.free_zone_name).toBeNull();
    expect(body.weekly_hours).toBeNull();
  });
});

describe("normaliseNumber", () => {
  it("reads digits typed on Arabic, Hindi, Bengali and Malayalam keyboards", () => {
    expect(normaliseNumber("١٬٨٠٠")).toBe("1800");
    expect(normaliseNumber("۲۲۰۰")).toBe("2200");
    expect(normaliseNumber("१८००")).toBe("1800");
    expect(normaliseNumber("১,৮০০")).toBe("1800");
    expect(normaliseNumber("൧൮൦൦")).toBe("1800");
    expect(normaliseNumber(" 1,800.50 ")).toBe("1800.50");
  });
});

describe("serverErrors", () => {
  it("maps field and model errors from a 422", () => {
    const got = serverErrors([
      { loc: ["total_wage_aed"], msg: "Input should be greater than 0" },
      { loc: [], msg: "Value error, basic wage cannot exceed total wage" },
    ]);
    expect(got.fields).toEqual({ total_wage_aed: "confirm.invalid" });
    expect(got.form).toEqual(["confirm.basicAboveTotal"]);
  });

  it("falls back to a general message", () => {
    expect(serverErrors("nope")).toEqual({ fields: {}, form: ["confirm.fixErrors"] });
  });
});
