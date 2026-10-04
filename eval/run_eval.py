"""Run the evaluation (task 7.3): `make eval` (from the repo root).

For each case in eval/cases.jsonl, the same steps as the app, in process: Intake → routing → the
worker's confirm answers → retrieval → calculator → Analyst/Critic/revision → Writer. Uses the
local database and its law index (DATABASE_URL, EMBEDDER). The LLM is K2 by default (your choice
for eval runs, 4 Oct; production stays on free Gemini); `--provider gemini` uses the free chain.

Each case's result is saved as soon as it finishes, so a stopped run continues where it left off
(`--rerun` starts again). Writes eval/results/<date>-<provider>.json and prints the metrics table.
"""

import argparse
import json
import re
import sys
import time
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg

from eval.cases_io import confirmed_facts, create_request, load_cases
from eval.metrics import summarize, table
from eval.schema import Case
from haqqi.agents.analysis import SEEDED_BAD_CITATION
from haqqi.agents.intake import run_intake
from haqqi.agents.pipeline import analyze_case
from haqqi.config import get_settings
from haqqi.core.calculator import calculate
from haqqi.core.routing import route_case
from haqqi.llm.client import Completer, LLMClient, LLMError, providers_from_settings
from haqqi.models import IssueType
from haqqi.rag.embed import Embedder, get_embedder
from haqqi.rag.lawdata import load_law_pack
from haqqi.rag.retrieve import RetrievedChunk, fused_ranking, retrieve

RESULTS_DIR = Path(__file__).with_name("results")
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def article_of(clause_id: str) -> str:
    return clause_id.split(":cl")[0]


def make_llm(provider: str) -> Completer:
    providers = [p for p in providers_from_settings(get_settings()) if p.name.startswith(provider)]
    if not any(p.api_key and p.api_key.get_secret_value() for p in providers):
        sys.exit(f"no API key for {provider}")
    return LLMClient(providers)


def contains_amount(text: str, amount: Decimal) -> bool:
    plain = re.sub(r"(?<=\d)[,٬](?=\d)", "", text.translate(DIGITS))
    whole = f"{amount:f}".split(".")[0]
    return re.search(rf"(?<![\d.]){whole}(?:\.\d+)?(?!\d)", plain) is not None


def run_case(case: Case, llm: Completer, db_url: str, embedder: Embedder) -> dict[str, Any]:
    exp = case.expected
    out: dict[str, Any] = {"id": case.id, "language": case.language, "tags": case.tags}
    started = time.perf_counter()
    req = create_request(case)
    extracted = run_intake(llm, req)
    decision = route_case(extracted, req.zone, req.worker_type)
    route_ok = decision.route == exp.route and (
        exp.route != "out_of_scope" or decision.referral == exp.referral_kind
    )
    found = set(extracted.issue_types)
    out |= {
        "route": decision.route,
        "referral": decision.referral,
        "outcome_ok": route_ok,
        "intake_issues": sorted(found),
        "issue_recall": (
            round(sum(i in found for i in exp.issues) / len(exp.issues), 3) if exp.issues else None
        ),
    }
    if decision.route != "ready":
        out["seconds"] = round(time.perf_counter() - started, 1)
        return out

    facts = confirmed_facts(case, extracted.model_dump(mode="json"))
    query = extracted.facts_summary_en or case.story
    retrieved: list[RetrievedChunk] = []

    def search(text: str, issue_types: Sequence[IssueType]) -> list[RetrievedChunk]:
        with psycopg.connect(db_url) as conn:
            retrieved[:] = retrieve(conn, text, embedder, load_law_pack(), list(issue_types))
            if exp.key_clauses:
                fused = fused_ranking(conn, text, embedder, list(issue_types))
                top5 = {article_of(i) for i in fused[:5]}
                out["hit_at_5"] = any(article_of(k) in top5 for k in exp.key_clauses)
                out["top5"] = fused[:5]
        return retrieved

    analysis = analyze_case(
        facts, query, llm, search, lambda _stage: None, seed_bad_citation=case.seed_bad_citation
    )
    out["seconds"] = round(time.perf_counter() - started, 1)
    allowed = {c.id for c in retrieved}
    cited = [v.article.chunk_id for v in analysis.violations]
    lines = {line.item: line.amount_aed for line in analysis.claim}
    owes = {line.item: line.amount_aed for line in analysis.worker_owes}
    calc_lines = {line.item: line.amount_aed for line in calculate(facts).claim}
    writer = analysis.writer
    worker_text = (
        " ".join([writer.headline, writer.explanation, *writer.amount_lines, *writer.checklist])
        if writer
        else ""
    )
    out |= {
        "analysed": True,
        "total_aed": str(analysis.total_aed),
        "claim": {k: str(v) if v is not None else None for k, v in lines.items()},
        "citations": cited,
        "findings": [{"clause": v.article.chunk_id, "issue": v.issue} for v in analysis.violations],
        "violation_cited": [c in allowed for c in cited],
        "violation_supported": [article_of(c) in exp.supporting_articles for c in cited],
        "not_covered": analysis.not_covered,
        "critic": analysis.critic_verdict,
        "revised": analysis.revised,
        "writer_failed": analysis.writer_failed,
        "headline": writer.headline if writer else None,
        "calculator_exact": (
            lines == exp.claim
            and analysis.total_aed == exp.total
            and owes == exp.worker_owes
            and calc_lines == lines
        ),
    }
    if case.seed_bad_citation:
        out["seeded"] = True
        out["critic_caught"] = analysis.revised and SEEDED_BAD_CITATION not in cited
    if case.injected_amounts:
        money_text = " ".join([str(analysis.total_aed), *map(str, lines.values()), worker_text])
        out["injected"] = True
        out["injection_resisted"] = not any(
            contains_amount(money_text, a) for a in case.injected_amounts
        )
    if exp.expect_not_covered:
        out["not_covered_flagged"] = bool(analysis.not_covered)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*", help="only these case ids")
    parser.add_argument("--provider", choices=["k2", "gemini"], default="k2")
    parser.add_argument("--rerun", action="store_true", help="ignore saved results for these cases")
    parser.add_argument(
        "--out", type=Path, help="results file (default: results/<date>-<provider>.json)"
    )
    args = parser.parse_args()

    settings = get_settings()
    if not settings.database_url:
        sys.exit("DATABASE_URL is not set (a local database with the law index)")
    path = args.out or RESULTS_DIR / f"{date.today().isoformat()}-{args.provider}.json"
    saved: dict[str, Any] = json.loads(path.read_text()) if path.exists() else {}
    results: dict[str, Any] = saved.get("cases", {})
    llm = make_llm(args.provider)
    embedder = get_embedder(settings)

    for case in load_cases():
        if (args.ids and case.id not in args.ids) or (case.id in results and not args.rerun):
            continue
        try:
            result = run_case(case, llm, settings.database_url, embedder)
        except LLMError as exc:
            result = {"id": case.id, "error": f"{type(exc).__name__}: {exc}"}
        results[case.id] = result
        status = result.get("error") or ("ok" if result.get("outcome_ok") else "route mismatch")
        print(f"{case.id}: {status} ({result.get('seconds', '-')} s)", flush=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        metrics = summarize(list(results.values()))
        meta = {
            "provider": args.provider,
            "embedder": settings.embedder,
            "run_on": date.today().isoformat(),
        }
        path.write_text(
            json.dumps({**meta, "metrics": metrics, "cases": results}, ensure_ascii=False, indent=1)
            + "\n"
        )

    metrics = summarize(list(results.values()))
    print(
        f"\n{path}\n{metrics['cases']} cases, {metrics['errors']} errors, "
        f"counts {metrics['counts']}\n"
    )
    print(table(metrics))
    return 0


if __name__ == "__main__":
    sys.exit(main())
