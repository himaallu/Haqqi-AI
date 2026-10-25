/** Pure helpers for the pitch demo: what to ask next, what to send, which prepared answer fits. */

import type { Citation, ExtractedFacts } from "@/lib/types";

import type { Strings } from "./strings";

/** Mirrors backend/haqqi/api/demo.py `CitedClause`. */
export type LawClause = {
  chunk_id: string;
  ref_en: string;
  ref_ar: string;
  title: string;
  text_en: string;
  text_ar: string;
};
export type Contact = { label: string; number: string };
/** Mirrors backend/haqqi/api/demo.py `AskResponse`. */
export type AskReply = {
  kind: "answer" | "unsure" | "off_topic";
  headline: string;
  answer: string;
  citations: LawClause[];
  suggest_case: boolean;
  safety: boolean;
  contacts: Contact[];
};

// English only, like the backend's check (haqqi/agents/ask.py); the model's flag covers other languages.
const DANGER = /\b(beat(s|ing|en)?|hit(s|ting)? me|locked (in|up)|lock(s|ed)? (me|us)|no food|no water|traffick\w*|forced to work|sexual(ly)?|rape\w*|threaten\w*|kill)\b/i;

// Arabic too (today's demo languages are English and Arabic). No \b here: JavaScript's \b only knows ASCII letters.
const DANGER_AR = /(يضرب|يضربنا|ضربني|ضرب|حبس|محبوس|محبوسين|أغلق\s*علي|اتجار|تحرش|اعتداء|يهدد|تهديد|بدون\s*طعام|بلا\s*طعام|بدون\s*ماء|بلا\s*ماء|العمل\s*القسري)/;

export function isDanger(text: string): boolean {
  return DANGER.test(text) || DANGER_AR.test(text);
}

/** The prepared answer whose keywords best match `text`, or null. */
export function matchPrepared<T extends { keys: string[] }>(text: string, prepared: T[]): T | null {
  const lower = text.toLowerCase();
  let best: T | null = null;
  let bestScore = 0;
  for (const item of prepared) {
    const score = item.keys.filter((k) => lower.includes(k.toLowerCase())).length;
    if (score > bestScore) {
      best = item;
      bestScore = score;
    }
  }
  return best;
}

/** "Art. 13(2)" from "Art. 13(2), Federal Decree-Law No. 33 of 2021"; Cabinet Resolution clauses get a "CR" prefix. */
export function shortRef(refEn: string): string {
  const head = refEn.split(",")[0];
  return refEn.includes("Cabinet Resolution") ? `CR ${head}` : head;
}

export function citationLabel(c: Citation): string {
  const ref = c.clause_no === null ? `${c.article_no}` : `${c.article_no}(${c.clause_no})`;
  return c.law_id === "cr1-2022" ? `CR Art. ${ref}` : `Art. ${ref}`;
}

// The case flow asks only for these, in this order, and only when the story didn't already answer them.
export type Field =
  | "zone"
  | "worker_type"
  | "emirate"
  | "termination"
  | "start_date"
  | "end_date"
  | "total_wage_aed"
  | "basic_wage_aed";
export const FIELD_ORDER: Field[] = [
  "zone",
  "worker_type",
  "emirate",
  "termination",
  "start_date",
  "end_date",
  "total_wage_aed",
  "basic_wage_aed",
];
export type Known = Partial<Record<string, string>>;

/** Extracted facts as strings, skipping anything the model left empty. */
export function knownFromExtracted(extracted: Partial<ExtractedFacts>): Known {
  const known: Known = {};
  for (const [key, value] of Object.entries(extracted)) {
    if (value !== null && value !== undefined && value !== "" && !Array.isArray(value) && typeof value !== "boolean") {
      known[key] = String(value);
    }
  }
  return known;
}

export function nextField(known: Known): Field | null {
  for (const field of FIELD_ORDER) {
    if (field === "end_date" && (known.termination ?? "still_employed") === "still_employed") continue;
    if (!known[field]) return field;
  }
  return null;
}

/**
 * PATCH body: only what the worker answered or changed. The API keeps extracted values for anything left out,
 * so a null here would erase a fact the story gave.
 */
export function patchBody(answers: Known): Record<string, string> {
  const body: Record<string, string> = {};
  for (const [key, value] of Object.entries(answers)) if (value) body[key] = value;
  if (body.termination === "still_employed") delete body.end_date;
  return body;
}

export type Chip = { value: string; label: string };

export function chipsFor(field: Field, s: Strings): Chip[] {
  switch (field) {
    case "zone":
      return [
        { value: "mainland", label: s.zoneMainland },
        { value: "free_zone", label: s.zoneFree },
        { value: "difc", label: "DIFC" },
        { value: "adgm", label: "ADGM" },
      ];
    case "worker_type":
      return [
        { value: "private_sector", label: s.workerCompany },
        { value: "domestic", label: s.workerHome },
      ];
    case "emirate":
      return Object.entries(EMIRATE_NAMES).map(([value, label]) => ({ value, label }));
    case "termination":
      return [
        { value: "still_employed", label: s.termStill },
        { value: "employer", label: s.termEmployer },
        { value: "resigned", label: s.termResigned },
      ];
    default:
      return [];
  }
}

export const EMIRATE_NAMES: Record<string, string> = {
  abu_dhabi: "Abu Dhabi",
  dubai: "Dubai",
  sharjah: "Sharjah",
  ajman: "Ajman",
  umm_al_quwain: "Umm Al Quwain",
  ras_al_khaimah: "Ras Al Khaimah",
  fujairah: "Fujairah",
};

export function question(field: Field, s: Strings): string {
  return {
    zone: s.qZone,
    worker_type: s.qWorker,
    emirate: s.qEmirate,
    termination: s.qTermination,
    start_date: s.qStart,
    end_date: s.qEnd,
    total_wage_aed: s.qTotal,
    basic_wage_aed: s.qBasic,
  }[field];
}

export function kindOf(field: Field): "chips" | "date" | "money" {
  if (field === "start_date" || field === "end_date") return "date";
  if (field === "total_wage_aed" || field === "basic_wage_aed") return "money";
  return "chips";
}

/** Digits typed on any keyboard (Arabic-Indic and Devanagari included) → a plain number string, or null. */
export function parseAmount(text: string): string | null {
  const western = text
    .replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 0x660))
    .replace(/[۰-۹]/g, (d) => String(d.charCodeAt(0) - 0x6f0))
    .replace(/[०-९]/g, (d) => String(d.charCodeAt(0) - 0x966))
    .replace(/[,\s٬]/g, "");
  const match = western.match(/\d+(\.\d+)?/);
  return match && Number(match[0]) > 0 ? match[0] : null;
}

export function isoDate(year: number, month: number, day: number | null): string {
  return `${year}-${String(month).padStart(2, "0")}-${String(day ?? 1).padStart(2, "0")}`;
}

/** How a known value reads on the facts card. */
export function display(field: string, value: string, s: Strings, locale: string): string {
  if (field === "emirate") return EMIRATE_NAMES[value] ?? value;
  const chip = (["zone", "worker_type", "termination"] as Field[]).includes(field as Field)
    ? chipsFor(field as Field, s).find((c) => c.value === value)
    : undefined;
  if (chip) return chip.label;
  if (field.endsWith("_date")) {
    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime())
      ? value
      : date.toLocaleDateString(locale, { day: "numeric", month: "long", year: "numeric", numberingSystem: "latn" });
  }
  if (field.endsWith("_aed")) return `AED ${Number(value).toLocaleString("en-US")}`;
  if (field.startsWith("notice_days")) return `${value} ${s.days}`;
  return value;
}
