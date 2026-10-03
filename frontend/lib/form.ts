/** The confirm-facts form (task 4.4): CaseView → form values → PATCH body, plus validation. */

import type { MessageKey } from "./i18n/translate";
import {
  CONTRACT_TYPES,
  EMIRATES,
  TERMINATIONS,
  WORKER_TYPES,
  ZONES,
  type CaseView,
} from "./types";

export type FieldName =
  | "emirate"
  | "zone"
  | "free_zone_name"
  | "worker_type"
  | "contract_type"
  | "weekly_hours"
  | "start_date"
  | "total_wage_aed"
  | "basic_wage_aed"
  | "months_unpaid"
  | "deducted_amount_aed"
  | "deducted_monthly_aed"
  | "termination"
  | "end_date"
  | "notice_days_contract"
  | "notice_days_given"
  | "unused_leave_days"
  | "unpaid_absence_days";

export type Section = "job" | "pay" | "end" | "other";
type Kind = "select" | "text" | "date" | "money" | "int" | "decimal";
/** What an empty answer means: the field must be filled, it is sent as null, or the backend default applies. */
type Empty = "required" | "null" | { default: string | number };

export type FieldSpec = {
  name: FieldName;
  section: Section;
  kind: Kind;
  label: MessageKey;
  help?: MessageKey;
  options?: readonly string[];
  optionPrefix?: string; // catalog prefix for option labels, e.g. "emirate"
  empty: Empty;
  /** Shown only when this returns true; hidden fields are sent as null. */
  visible?: (v: FormValues) => boolean;
};

export type FormValues = Record<FieldName, string>;
export type FieldErrors = Partial<Record<FieldName, MessageKey>>;

const endedJob = (v: FormValues) => v.termination !== "still_employed";

export const FIELDS: FieldSpec[] = [
  { name: "emirate", section: "job", kind: "select", label: "field.emirate", options: EMIRATES, optionPrefix: "emirate", empty: "required" },
  { name: "zone", section: "job", kind: "select", label: "field.zone", options: ZONES, optionPrefix: "zone", empty: "required" },
  { name: "free_zone_name", section: "job", kind: "text", label: "field.freeZoneName", empty: "null", visible: (v) => v.zone === "free_zone" },
  { name: "worker_type", section: "job", kind: "select", label: "field.workerType", options: WORKER_TYPES, optionPrefix: "workerType", empty: "required" },
  { name: "contract_type", section: "job", kind: "select", label: "field.contractType", options: CONTRACT_TYPES, optionPrefix: "contractType", empty: { default: "full_time" } },
  { name: "weekly_hours", section: "job", kind: "decimal", label: "field.weeklyHours", empty: "null", visible: (v) => v.contract_type === "part_time" },
  { name: "start_date", section: "job", kind: "date", label: "field.startDate", empty: "required" },
  { name: "basic_wage_aed", section: "pay", kind: "money", label: "field.basicWage", help: "field.basicWageHelp", empty: "required" },
  { name: "total_wage_aed", section: "pay", kind: "money", label: "field.totalWage", help: "field.totalWageHelp", empty: "required" },
  { name: "months_unpaid", section: "pay", kind: "int", label: "field.monthsUnpaid", empty: { default: 0 } },
  { name: "deducted_amount_aed", section: "pay", kind: "money", label: "field.deductedAmount", empty: { default: "0" } },
  { name: "deducted_monthly_aed", section: "pay", kind: "money", label: "field.deductedMonthly", empty: "null" },
  { name: "termination", section: "end", kind: "select", label: "field.termination", options: TERMINATIONS, optionPrefix: "termination", empty: "required" },
  { name: "end_date", section: "end", kind: "date", label: "field.endDate", empty: "required", visible: endedJob },
  { name: "notice_days_contract", section: "end", kind: "int", label: "field.noticeDaysContract", empty: { default: 30 }, visible: endedJob },
  { name: "notice_days_given", section: "end", kind: "int", label: "field.noticeDaysGiven", empty: { default: 0 }, visible: endedJob },
  { name: "unused_leave_days", section: "other", kind: "int", label: "field.unusedLeaveDays", empty: "null" },
  { name: "unpaid_absence_days", section: "other", kind: "int", label: "field.unpaidAbsenceDays", empty: { default: 0 } },
];

export const SECTIONS: { id: Section; label: MessageKey }[] = [
  { id: "job", label: "section.job" },
  { id: "pay", label: "section.pay" },
  { id: "end", label: "section.end" },
  { id: "other", label: "section.other" },
];

const FIELD_NAMES = new Set<string>(FIELDS.map((f) => f.name));

export function isVisible(field: FieldSpec, values: FormValues): boolean {
  return field.visible ? field.visible(values) : true;
}

/** Pre-fills from the confirmed facts if the worker already confirmed, else from what the Intake read. */
export function initialValues(view: CaseView): { values: FormValues; prefilled: Set<FieldName> } {
  const source: Record<string, unknown> = view.confirmed ?? view.extracted;
  const values = {} as FormValues;
  const prefilled = new Set<FieldName>();
  for (const { name } of FIELDS) {
    const raw = source[name];
    values[name] = raw === null || raw === undefined ? "" : String(raw);
    if (values[name] !== "" && !view.confirmed) prefilled.add(name);
  }
  return { values, prefilled };
}

// Phone keyboards may type Arabic-Indic, Devanagari, Bengali or Malayalam digits.
const DIGIT_ZEROS = [0x0660, 0x06f0, 0x0966, 0x09e6, 0x0d66];

export function normaliseNumber(text: string): string {
  let out = "";
  for (const ch of text.trim()) {
    const code = ch.codePointAt(0) ?? 0;
    const zero = DIGIT_ZEROS.find((z) => code >= z && code <= z + 9);
    if (zero !== undefined) out += String(code - zero);
    else if (ch === "٫") out += ".";
    else if (ch !== "," && ch !== "٬" && ch !== " ") out += ch;
  }
  return out;
}

const PATTERNS: Partial<Record<Kind, RegExp>> = {
  money: /^\d{1,7}(\.\d{1,2})?$/,
  decimal: /^\d{1,3}(\.\d{1,2})?$/,
  int: /^\d{1,5}$/,
  date: /^\d{4}-\d{2}-\d{2}$/,
};

export type Validation = { fields: FieldErrors; form: MessageKey[] };

export function validate(values: FormValues): Validation {
  const fields: FieldErrors = {};
  for (const field of FIELDS) {
    if (!isVisible(field, values)) continue;
    const raw = values[field.name].trim();
    if (!raw) {
      if (field.empty === "required") fields[field.name] = "confirm.required";
      continue;
    }
    const pattern = PATTERNS[field.kind];
    const text = field.kind === "date" ? raw : normaliseNumber(raw);
    if (pattern && !pattern.test(text)) fields[field.name] = "confirm.invalid";
  }
  const form: MessageKey[] = [];
  const basic = Number(normaliseNumber(values.basic_wage_aed));
  const total = Number(normaliseNumber(values.total_wage_aed));
  if (!fields.basic_wage_aed && !fields.total_wage_aed && basic > total) {
    fields.basic_wage_aed = "confirm.basicAboveTotal";
    form.push("confirm.basicAboveTotal");
  }
  if (endedJob(values) && values.end_date && values.start_date && values.end_date < values.start_date) {
    fields.end_date = "confirm.endBeforeStart";
    form.push("confirm.endBeforeStart");
  }
  if (Object.keys(fields).length && !form.length) form.push("confirm.fixErrors");
  return { fields, form };
}

/** The PATCH body. Every field is sent, so a cleared answer replaces what the Intake read. */
export function toPatch(values: FormValues): Record<string, string | number | null> {
  const body: Record<string, string | number | null> = {};
  for (const field of FIELDS) {
    const raw = values[field.name].trim();
    if (!isVisible(field, values) || (!raw && field.empty === "null")) {
      body[field.name] = null;
    } else if (!raw) {
      body[field.name] = typeof field.empty === "object" ? field.empty.default : null;
    } else if (field.kind === "int") {
      body[field.name] = Number.parseInt(normaliseNumber(raw), 10);
    } else if (field.kind === "money" || field.kind === "decimal") {
      body[field.name] = normaliseNumber(raw); // a decimal string; the backend reads it as Decimal
    } else {
      body[field.name] = raw;
    }
  }
  return body;
}

type PydanticError = { loc?: unknown[]; msg?: string };

/** Maps a 422 `detail` from PATCH onto the form. */
export function serverErrors(detail: unknown): Validation {
  const fields: FieldErrors = {};
  const form: MessageKey[] = [];
  for (const err of Array.isArray(detail) ? (detail as PydanticError[]) : []) {
    const name = [...(err.loc ?? [])].reverse().find((part) => typeof part === "string" && FIELD_NAMES.has(part));
    const msg = err.msg ?? "";
    if (typeof name === "string") fields[name as FieldName] = "confirm.invalid";
    else if (msg.includes("basic wage cannot exceed")) form.push("confirm.basicAboveTotal");
    else if (msg.includes("before start_date")) form.push("confirm.endBeforeStart");
    else if (msg.includes("end_date is required")) fields.end_date = "confirm.required";
  }
  if (!form.length) form.push("confirm.fixErrors");
  return { fields, form };
}
