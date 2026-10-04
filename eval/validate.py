"""Check eval/cases.jsonl (tasks 7.1–7.2): `make eval-validate`.

Every row must parse, use real clause ids, make a valid form request, and (for cases that reach
analysis) describe confirmable facts. The hand-worked total must equal the sum of its hand-worked
lines. Prints counts by route, issue type and language. Exits non-zero on any problem.
"""

import sys
from collections import Counter
from decimal import Decimal

from eval.cases_io import confirmed_facts, create_request, load_cases
from haqqi.rag.lawdata import load_chunks


def problems() -> tuple[list[str], list]:  # type: ignore[type-arg]
    cases = load_cases()
    clause_ids = {c.id for c in load_chunks()}
    article_ids = {cid.split(":cl")[0] for cid in clause_ids}
    errors: list[str] = []
    seen: set[str] = set()
    for case in cases:
        where = case.id
        if case.id in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(case.id)
        exp = case.expected
        try:
            create_request(case)
        except ValueError as exc:
            errors.append(f"{where}: form is not a valid request: {exc}")
        errors += [f"{where}: unknown clause {c}" for c in exp.key_clauses if c not in clause_ids]
        errors += [
            f"{where}: unknown article {a}" for a in exp.supporting_articles if a not in article_ids
        ]
        if exp.route == "out_of_scope" and not exp.referral_kind:
            errors.append(f"{where}: out_of_scope needs referral_kind")
        if exp.route == "ready":
            try:
                confirmed_facts(case)
            except ValueError as exc:
                errors.append(f"{where}: form + confirm do not describe the case: {exc}")
            lines = sum((v for v in exp.claim.values() if v is not None), Decimal(0))
            if exp.total is None or lines != exp.total:
                errors.append(f"{where}: total {exp.total} != sum of claim lines {lines}")
            if exp.max_total is not None and exp.total is not None and exp.total > exp.max_total:
                errors.append(f"{where}: total above max_total")
        for amount in case.injected_amounts:
            if amount in exp.claim.values() or amount == exp.total:
                errors.append(f"{where}: an injected amount is also an expected amount")
    return errors, cases


def main() -> int:
    errors, cases = problems()
    routes = Counter(c.expected.route for c in cases)
    issues = Counter(i for c in cases for i in c.expected.issues)
    languages = Counter(c.language for c in cases)
    print(f"{len(cases)} cases: " + ", ".join(f"{k} {v}" for k, v in sorted(routes.items())))
    print("issues: " + ", ".join(f"{k} {v}" for k, v in issues.most_common()))
    print("languages: " + ", ".join(f"{k} {v}" for k, v in languages.most_common()))
    print(
        f"seeded citations {sum(c.seed_bad_citation for c in cases)}, "
        f"injection {sum(bool(c.injected_amounts) or 'injection' in c.tags for c in cases)}"
    )
    for e in errors:
        print("ERROR", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
