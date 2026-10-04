"""Task 6.3: run one harness case per language through the API and record what came back.

Usage (from backend/, with a local server on :8000):
    uv run python ../eval/language_check.py [TC-01 TC-04 ...]

For each case: create → confirm → analyze (like the UI), then the complaint PDF. Records the route, the issues the
Intake found, citations, the total, whether the worker-facing text and the letter translation are in the worker's
script, latency, and the fonts embedded in the PDF. Writes eval/results/language_check.json and the PDFs to
docs/language_check/. Fluency is not judged here: that needs a native or fluent reader.
"""

import json
import re
import sys
import time
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import httpx
from pypdf import PdfReader

API = "http://localhost:8000"
ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results" / "language_check.json"
PDF_DIR = ROOT / "docs" / "language_check"

# Stories and form fields from legacy/n8n/Haqqi Test.json (test data, no real people).
CASES: list[dict[str, object]] = [
    {
        "id": "TC-01", "language": "hi", "expected": ["unpaid_wages"],
        "story": "मैं अजमान में एक कंस्ट्रक्शन कंपनी में हेल्पर का काम करता हूँ। पिछले 3 महीने से मेरी तनख्वाह नहीं मिली है। "
        "कंपनी हर बार बोलती है अगले महीने देंगे। मैं अभी भी वहीं काम कर रहा हूँ।",
        "form": {"emirate": "ajman", "start_date": "2023-02-01", "basic_wage_aed": "1200", "total_wage_aed": "1800"},
    },
    {
        "id": "TC-04", "language": "ml", "expected": ["illegal_deduction"],
        "story": "എന്റെ salary-ൽ നിന്ന് ഓരോ മാസവും 600 ദിർഹം cut ചെയ്യുന്നു. No letter, no consent. 4 മാസമായി ഇങ്ങനെ.",
        "form": {"emirate": "dubai", "start_date": "2025-01-10", "basic_wage_aed": "2500", "total_wage_aed": "3000"},
    },
    {
        "id": "TC-05", "language": "tl", "expected": ["document_retention"],
        "story": "Kinuha ng employer ko ang passport ko noong nagsimula ako at ayaw nilang ibalik kahit hinihingi ko. "
        "Gusto ko nang lumipat ng trabaho.",
        "form": {"emirate": "dubai", "start_date": "2025-03-01", "basic_wage_aed": "2500", "total_wage_aed": "3200"},
    },
    {
        "id": "TC-06", "language": "bn", "expected": ["overtime", "leave"],
        "story": "আমি একটি ওয়ার্কশপে কাজ করি। প্রতিদিন ১২ ঘণ্টা কাজ করি কিন্তু ওভারটাইমের কোনো টাকা পাই না। "
        "দুই বছর ধরে কোনো বার্ষিক ছুটিও পাইনি।",
        "form": {"emirate": "fujairah", "start_date": "2024-01-15", "basic_wage_aed": "1500", "total_wage_aed": "2000"},
    },
    {
        "id": "TC-23", "language": "ar", "expected": ["unpaid_wages"], "max_total": "5000",
        "story": "أعمل في شركة مقاولات في رأس الخيمة منذ يناير 2024. لم أستلم راتب شهرين، يوليو وأغسطس. ما زلت أعمل في الشركة.",
        "form": {"emirate": "ras_al_khaimah", "start_date": "2024-01-15", "basic_wage_aed": "1800",
                 "total_wage_aed": "2500"},
    },
    {
        "id": "TC-08", "language": "ne", "expected": [], "expect_referral": "domestic",
        "story": "म दुबईमा एउटा घरमा घरेलु कामदारको रूपमा काम गर्छु। दुई महिनादेखि मलाई तलब दिइएको छैन।",
        "form": {"emirate": "dubai", "worker_type": "domestic", "start_date": "2025-06-01", "basic_wage_aed": "1200",
                 "total_wage_aed": "1200"},
    },
    {
        "id": "TC-02", "language": "ur", "expected": ["termination", "notice_pay"], "total": "6229.59",
        "story": "میں ابوظبی میں ایک سپر مارکیٹ میں کیشیئر تھی۔ 20 ستمبر کو مینیجر نے کہا کہ آج سے آپ کی نوکری ختم ہے اور کوئی "
        "نوٹس نہیں دیا گیا۔ میرے معاہدے میں 30 دن کا نوٹس لکھا ہے۔",
        "form": {"emirate": "abu_dhabi", "start_date": "2024-06-01", "end_date": "2026-09-20", "basic_wage_aed": "2000",
                 "total_wage_aed": "3000"},
    },
    {
        "id": "TC-03", "language": "en", "expected": ["gratuity"], "total": "16056.85",
        "story": "I worked at a hotel in Dubai for six years and resigned with proper notice. The company says my "
        "end-of-service gratuity is AED 6,000. I think this is too low.",
        "form": {"emirate": "dubai", "start_date": "2020-08-01", "end_date": "2026-08-31", "basic_wage_aed": "3500",
                 "total_wage_aed": "5000"},
    },
]

# Answers a worker would give on the confirm form when the Intake leaves a required field empty.
CONFIRM_DEFAULTS: dict[str, object] = {"contract_type": "full_time", "months_unpaid": 0, "notice_days_given": 0}

SCRIPTS = {
    "hi": r"[ऀ-ॿ]", "ne": r"[ऀ-ॿ]", "ur": r"[؀-ۿ]", "ar": r"[؀-ۿ]",
    "ml": r"[ഀ-ൿ]", "bn": r"[ঀ-৿]", "en": r"[A-Za-z]", "tl": r"[A-Za-z]",
}
LETTERS = re.compile(r"[^\W\d_]")


def script_share(text: str, language: str) -> float:
    """Share of letters in the worker's script (Latin languages: share of Latin letters)."""
    letters = LETTERS.findall(text)
    if not letters:
        return 0.0
    return round(sum(1 for ch in letters if re.match(SCRIPTS[language], ch)) / len(letters), 2)


def sse(body: str) -> list[tuple[str, dict[str, object]]]:
    events = []
    for block in body.strip().split("\n\n"):
        name, data = block.split("\n", 1)
        events.append((name.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return events


def pdf_fonts(data: bytes) -> list[str]:
    fonts = set()
    for page in PdfReader(BytesIO(data)).pages:
        for font in (page["/Resources"].get("/Font") or {}).values():
            fonts.add(str(font.get_object()["/BaseFont"]).split("+")[-1])
    return sorted(fonts)


def run(case: dict[str, object], client: httpx.Client) -> dict[str, object]:
    lang = str(case["language"])
    form = {"zone": "mainland", "worker_type": "private_sector", **case["form"]}  # type: ignore[dict-item]
    out: dict[str, object] = {"id": case["id"], "language": lang, "expected": case["expected"]}
    started = time.perf_counter()

    created = client.post(f"{API}/v1/cases", json={"language": lang, "story": case["story"], **form})
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

    filled: dict[str, object] = {}
    confirmed = client.patch(f"{API}/v1/cases/{view['id']}", json={})
    while confirmed.status_code == 422:
        errors = confirmed.json()["detail"]
        fields = {str(e["loc"][-1]) for e in errors if isinstance(e, dict) and e.get("loc")}
        new = {f: CONFIRM_DEFAULTS[f] for f in fields if f in CONFIRM_DEFAULTS and f not in filled}
        if not new:
            return {**out, "error": f"confirm 422: {errors}"}
        filled |= new
        confirmed = client.patch(f"{API}/v1/cases/{view['id']}", json=filled)
    out["filled_on_confirm"] = filled

    events = sse(client.post(f"{API}/v1/cases/{view['id']}/analyze").text)
    out["stages"] = [name for name, _ in events]
    name, analysis = events[-1]
    out["seconds"] = round(time.perf_counter() - started, 1)
    if name != "done":
        return {**out, "error": f"analyze: {analysis}"}

    writer = analysis.get("writer") or {}
    worker_text = " ".join([writer.get("headline", ""), writer.get("explanation", ""), *writer.get("checklist", [])])
    out |= {
        "total_aed": analysis["total_aed"],
        "claim": {line["item"]: line["amount_aed"] for line in analysis["claim"]},
        "citations": sorted({v["article"]["chunk_id"] for v in analysis["violations"]}),
        "not_covered": analysis["not_covered"],
        "critic": analysis["critic_verdict"],
        "revised": analysis["revised"],
        "writer_failed": analysis.get("writer_failed", False),
        "headline": writer.get("headline"),
        "worker_text_script": script_share(worker_text, lang) if writer else None,
        "letter_translation_script": script_share(writer.get("letter_facts_translation", ""), lang) if writer else None,
        "letter_facts_ar_script": script_share(writer.get("letter_facts_ar", ""), "ar") if writer else None,
        "arabic_indic_digits": bool(re.search(r"[٠-٩۰-۹]", writer.get("letter_facts_ar", ""))) if writer else None,
    }
    if writer:
        pdf = client.post(f"{API}/v1/cases/{view['id']}/complaint", json={})
        out["pdf_status"] = pdf.status_code
        if pdf.status_code == 200:
            PDF_DIR.mkdir(parents=True, exist_ok=True)
            path = PDF_DIR / f"{str(case['id']).lower()}_{lang}.pdf"
            path.write_bytes(pdf.content)
            out |= {"pdf": str(path.relative_to(ROOT)), "pdf_fonts": pdf_fonts(pdf.content)}
    if "total" in case:
        out["total_matches_cases_md"] = Decimal(str(analysis["total_aed"])) == Decimal(str(case["total"]))
    if "max_total" in case:
        out["within_max_total"] = Decimal(str(analysis["total_aed"])) <= Decimal(str(case["max_total"]))
    return out


def main(ids: list[str]) -> None:
    results = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    with httpx.Client(timeout=300) as client:
        for case in CASES:
            if ids and case["id"] not in ids:
                continue
            result = run(case, client)
            results[str(case["id"])] = {**result, "run_on": time.strftime("%Y-%m-%d")}
            print(json.dumps(result, ensure_ascii=False))
            RESULTS.parent.mkdir(parents=True, exist_ok=True)
            RESULTS.write_text(json.dumps(results, ensure_ascii=False, indent=1) + "\n")
            time.sleep(10)  # spread the calls over the per-minute quota


if __name__ == "__main__":
    main(sys.argv[1:])
