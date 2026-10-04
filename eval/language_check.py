"""Task 6.3: run one case per language through the API and record what came back.

Usage (from backend/, with a local server on :8000):
    PYTHONPATH=.. uv run python -m eval.language_check [TC-01 TC-04 ...]

For each case (stories and form fields from eval/cases.jsonl): create → confirm → analyze, like the
UI, then the complaint PDF. Records the route, the issues the Intake found, citations, the total,
whether the worker-facing text and the letter translation are in the worker's script, latency and
the fonts embedded in the PDF. Writes eval/results/language_check.json and the PDFs to
docs/language_check/. Fluency is not judged here: that needs a native or fluent reader.
"""

import json
import re
import sys
import time
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
from pypdf import PdfReader

from eval.cases_io import load_cases
from eval.schema import Case

API = "http://localhost:8000"
ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results" / "language_check.json"
PDF_DIR = ROOT / "docs" / "language_check"

# One case per language, in the order they were run on 4 Oct.
LANGUAGE_CASES = ["TC-01", "TC-04", "TC-05", "TC-06", "TC-23", "TC-08", "TC-02", "TC-03"]

SCRIPTS = {
    "hi": r"[ऀ-ॿ]",
    "ne": r"[ऀ-ॿ]",
    "ur": r"[؀-ۿ]",
    "ar": r"[؀-ۿ]",
    "ml": r"[ഀ-ൿ]",
    "bn": r"[ঀ-৿]",
    "en": r"[A-Za-z]",
    "tl": r"[A-Za-z]",
}
LETTERS = re.compile(r"[^\W\d_]")


def script_share(text: str, language: str) -> float:
    """Share of letters in the worker's script (Latin languages: share of Latin letters)."""
    letters = LETTERS.findall(text)
    if not letters:
        return 0.0
    return round(sum(1 for ch in letters if re.match(SCRIPTS[language], ch)) / len(letters), 2)


def sse(body: str) -> list[tuple[str, dict[str, Any]]]:
    events = []
    for block in body.strip().split("\n\n"):
        name, data = block.split("\n", 1)
        events.append((name.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return events


def pdf_fonts(data: bytes) -> list[str]:
    fonts = set()
    for page in PdfReader(BytesIO(data)).pages:
        resources: Any = page["/Resources"]
        for font in (resources.get("/Font") or {}).values():
            fonts.add(str(font.get_object()["/BaseFont"]).split("+")[-1])
    return sorted(fonts)


def run(case: Case, client: httpx.Client) -> dict[str, Any]:
    lang = case.language
    body = {"language": lang, "story": case.story, "contract_text": case.contract_text, **case.form}
    out: dict[str, Any] = {"id": case.id, "language": lang, "expected": case.expected.issues}
    started = time.perf_counter()

    created = client.post(f"{API}/v1/cases", json=body)
    if created.status_code != 201:
        return {**out, "error": f"create HTTP {created.status_code}: {created.text[:200]}"}
    view = created.json()
    extracted = view["extracted"]
    out |= {
        "route": view["status"],
        "referral_kind": view["referral_kind"],
        "intake_issues": extracted["issue_types"],
        "intake_summary": extracted["facts_summary_en"],
        "missing_fields": view["missing_fields"],
    }
    if view["status"] == "out_of_scope":
        out["seconds"] = round(time.perf_counter() - started, 1)
        return out

    # The worker's confirm-form answers (the same ones the evaluation uses).
    confirmed = client.patch(f"{API}/v1/cases/{view['id']}", json=case.confirm)
    if confirmed.status_code != 200:
        return {**out, "error": f"confirm HTTP {confirmed.status_code}: {confirmed.text[:200]}"}

    events = sse(client.post(f"{API}/v1/cases/{view['id']}/analyze").text)
    out["stages"] = [name for name, _ in events]
    name, analysis = events[-1]
    out["seconds"] = round(time.perf_counter() - started, 1)
    if name != "done":
        return {**out, "error": f"analyze: {analysis}"}

    writer: dict[str, Any] = analysis.get("writer") or {}
    checklist: list[str] = writer.get("checklist", [])
    worker_text = " ".join([writer.get("headline", ""), writer.get("explanation", ""), *checklist])
    facts_ar = str(writer.get("letter_facts_ar", ""))
    out |= {
        "total_aed": analysis["total_aed"],
        "claim": {line["item"]: line["amount_aed"] for line in analysis["claim"]},
        "citations": sorted({v["article"]["chunk_id"] for v in analysis["violations"]}),
        "not_covered": analysis["not_covered"],
        "critic": analysis["critic_verdict"],
        "revised": analysis["revised"],
        "writer_failed": analysis.get("writer_failed", False),
        "headline": writer.get("headline"),
    }
    if writer:
        translation = str(writer.get("letter_facts_translation", ""))
        out |= {
            "worker_text_script": script_share(worker_text, lang),
            "letter_translation_script": script_share(translation, lang),
            "letter_facts_ar_script": script_share(facts_ar, "ar"),
            "arabic_indic_digits": bool(re.search(r"[٠-٩۰-۹]", facts_ar)),
        }
        pdf = client.post(f"{API}/v1/cases/{view['id']}/complaint", json={})
        out["pdf_status"] = pdf.status_code
        if pdf.status_code == 200:
            PDF_DIR.mkdir(parents=True, exist_ok=True)
            path = PDF_DIR / f"{case.id.lower()}_{lang}.pdf"
            path.write_bytes(pdf.content)
            out |= {"pdf": str(path.relative_to(ROOT)), "pdf_fonts": pdf_fonts(pdf.content)}
    total = Decimal(str(analysis["total_aed"]))
    if case.expected.total is not None:
        out["total_matches_cases_md"] = total == case.expected.total
    if case.expected.max_total is not None:
        out["within_max_total"] = total <= case.expected.max_total
    return out


def main(ids: list[str]) -> None:
    by_id = {c.id: c for c in load_cases()}
    results = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    with httpx.Client(timeout=300) as client:
        for case_id in ids or LANGUAGE_CASES:
            result = run(by_id[case_id], client)
            results[case_id] = {**result, "run_on": time.strftime("%Y-%m-%d")}
            print(json.dumps(result, ensure_ascii=False))
            RESULTS.parent.mkdir(parents=True, exist_ok=True)
            RESULTS.write_text(json.dumps(results, ensure_ascii=False, indent=1) + "\n")
            time.sleep(10)  # spread the calls over the per-minute quota


if __name__ == "__main__":
    main(sys.argv[1:])
