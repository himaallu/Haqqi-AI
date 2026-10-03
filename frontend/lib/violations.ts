import type { Citation, Confidence, Violation } from "@/lib/types";

export type Finding = { issue: string; confidence: Confidence; citations: Citation[] };

/**
 * One card per finding. The API returns one violation per cited clause, so a finding that cites
 * Art. 43(1) and 43(3) arrives twice with the same text; a repeated clause is shown once.
 */
export function groupViolations(violations: Violation[]): Finding[] {
  const byIssue = new Map<string, Finding>();
  for (const v of violations) {
    const finding = byIssue.get(v.issue);
    if (!finding) {
      byIssue.set(v.issue, { issue: v.issue, confidence: v.confidence, citations: [v.article] });
    } else if (!finding.citations.some((c) => c.chunk_id === v.article.chunk_id)) {
      finding.citations.push(v.article);
    }
  }
  return [...byIssue.values()];
}
