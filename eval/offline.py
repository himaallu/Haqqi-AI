"""Offline evaluation subset (task 7.4): `make eval-offline`. No LLM, no API key.

1. Calculator correctness: every analysed case's confirmed facts (form + confirm answers) through
   the calculator must equal the hand-worked lines, worker-owes lines and total exactly. Exits
   non-zero below 100%, so CI fails.
2. Retrieval hit@5, only when a local law index is reachable (DATABASE_URL and a real embedder).
   With no LLM there is no Intake, so the query is the worker's own story plus the case's
   expected issue types (a harder setting than the app's English summary). Otherwise it reports
   "skipped".
"""

import sys

import psycopg

from eval.cases_io import confirmed_facts, load_cases
from haqqi.config import get_settings
from haqqi.core.calculator import calculate
from haqqi.rag.embed import get_embedder
from haqqi.rag.retrieve import fused_ranking


def calculator_failures() -> tuple[int, list[str]]:
    failures, checked = [], 0
    for case in load_cases():
        if case.expected.route != "ready":
            continue
        checked += 1
        result = calculate(confirmed_facts(case))
        lines = {line.item: line.amount_aed for line in result.claim}
        owes = {line.item: line.amount_aed for line in result.worker_owes}
        exp = case.expected
        if lines != exp.claim or owes != exp.worker_owes or result.total_aed != exp.total:
            failures.append(f"{case.id}: got {lines} {owes} total {result.total_aed}")
    return checked, failures


def retrieval_hit_at_5() -> str:
    settings = get_settings()
    if not settings.database_url or settings.embedder == "hash":
        return "skipped (needs DATABASE_URL and EMBEDDER=cloudflare)"
    embedder = get_embedder(settings)
    hits = []
    with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
        for case in load_cases():
            if not case.expected.key_clauses:
                continue
            # No Intake offline: the expected issue types stand in for the Intake's.
            fused = fused_ranking(conn, case.story, embedder, case.expected.issues)
            top5 = {i.split(":cl")[0] for i in fused[:5]}
            hits.append(any(k.split(":cl")[0] in top5 for k in case.expected.key_clauses))
    share = sum(hits) / len(hits)
    return f"{sum(hits)}/{len(hits)} = {share:.0%} (story + issue types as the query)"


def main() -> int:
    checked, failures = calculator_failures()
    score = (checked - len(failures)) / checked if checked else 0.0
    print(f"calculator correctness: {checked - len(failures)}/{checked} = {score:.0%}")
    for failure in failures:
        print("  MISMATCH", failure)
    try:
        print(f"retrieval hit@5: {retrieval_hit_at_5()}")
    except psycopg.OperationalError as exc:
        print(f"retrieval hit@5: skipped (database unreachable: {type(exc).__name__})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
