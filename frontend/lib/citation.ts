import type { Citation } from "./types";

const LAW_NAMES: Record<string, string> = {
  "fdl33-2021": "Federal Decree-Law 33/2021",
  "cr1-2022": "Cabinet Resolution 1/2022",
};

/** "51(2)" for clause 2 of Article 51; "53" when the article has no clauses. */
export function articleRef(c: Citation): string {
  return c.clause_no === null ? String(c.article_no) : `${c.article_no}(${c.clause_no})`;
}

export function lawName(c: Citation): string {
  return LAW_NAMES[c.law_id] ?? c.law_id;
}
