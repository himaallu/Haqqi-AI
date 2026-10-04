"""The formal Arabic complaint to MOHRE, with the worker's language alongside (tasks 5.2-5.4).

Code builds every section from checked data; only the facts paragraph comes from the Writer:
- worker data: the confirmed CaseFacts, plus the identity fields typed at download (flag 8),
  which are printed and never stored or logged
- legal basis: the cited clause ids, rendered by `clause_ref`
- claims and total: the calculator's lines from the Analysis
- addressee, requests, attachments, date and signature: fixed text in strings/<lang>.json
The non-Arabic catalogs are drafts for native review (task 6.3).
"""

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from weasyprint import HTML

from haqqi.agents.messages import clause_ref
from haqqi.models import Analysis, CaseFacts, ClaimLine
from haqqi.pdf.fonts import FAMILIES, FONT_DIR, font_stack

PDF_DIR = Path(__file__).resolve().parent
STRINGS_DIR = PDF_DIR / "strings"
RTL = {"ar", "ur"}
BLANK = "." * 40  # a line to fill in by hand when an identity field is left empty

# Calculator item → catalog key. tests/pdf/test_letter.py checks every calculator item is here.
ITEM_KEYS = {
    "Unpaid wages": "unpaid_wages",
    "Deductions from wages": "deductions",
    "Notice pay": "notice_pay",
    "End-of-service gratuity": "gratuity",
    "Unused annual leave": "leave",
}


class LetterError(ValueError):
    """The case can't produce a complaint (out of scope, no findings, no Writer output)."""


@dataclass(frozen=True)
class Identity:
    """Typed by the worker at download. Printed into the PDF only: never stored or logged."""

    name: str | None = None
    labour_card: str | None = None
    employer: str | None = None


@dataclass(frozen=True)
class Pair:
    """One piece of text in Arabic and in the worker's language."""

    ar: str
    tr: str


@dataclass(frozen=True)
class ClaimRow:
    item: Pair
    amount: Pair


@dataclass(frozen=True)
class Letter:
    lang: str
    two_columns: bool
    tr_dir: str
    tr_font: str
    s_ar: dict[str, Any]
    s_tr: dict[str, Any]
    subject: Pair
    worker_rows: list[tuple[Pair, Pair]]
    facts: Pair
    legal_basis: list[Pair]
    claims: list[ClaimRow]
    total: Pair | None
    requests: list[Pair]
    attachments: list[Pair]
    date: str
    blank: str = BLANK


@cache
def strings(lang: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((STRINGS_DIR / f"{lang}.json").read_text(encoding="utf-8"))
    return data


def money_pair(amount: Decimal) -> Pair:
    figure = f"{amount:,.2f}"
    return Pair(ar=f"{figure} {strings('ar')['currency']}", tr=f"AED {figure}")


def build_letter(facts: CaseFacts, analysis: Analysis, identity: Identity, today: date) -> Letter:
    if not analysis.in_scope:
        raise LetterError("the case is out of scope: there is no complaint to MOHRE")
    if not analysis.violations and not analysis.claim:
        raise LetterError("the analysis found nothing to complain about")
    writer = analysis.writer
    if writer is None or not writer.letter_facts_ar:
        raise LetterError("the Writer's text is missing: run the analysis again")

    lang = facts.language
    ar, tr = strings("ar"), strings(lang)

    def pair(key: str) -> Pair:
        return Pair(ar=ar[key], tr=tr[key])

    items = [_item(line, ar, tr) for line in analysis.claim]
    subject = (
        Pair(
            ar=f"{ar['subject_prefix']} {'، '.join(i.ar for i in items)}",
            tr=f"{tr['subject_prefix']} {', '.join(i.tr for i in items)}",
        )
        if items
        else Pair(
            ar=f"{ar['subject_prefix']} {ar['subject_general']}",
            tr=f"{tr['subject_prefix']} {tr['subject_general']}",
        )
    )

    def same(value: str | None) -> Pair:
        text = value.strip() if value and value.strip() else BLANK
        return Pair(text, text)

    end = same(facts.end_date.isoformat()) if facts.end_date is not None else pair("still_employed")
    worker_rows = [
        (pair("name"), same(identity.name)),
        (pair("labour_card"), same(identity.labour_card)),
        (pair("employer"), same(identity.employer)),
        (
            pair("emirate_label"),
            Pair(ar["emirate"][facts.emirate.value], tr["emirate"][facts.emirate.value]),
        ),
        (
            pair("contract_type"),
            Pair(ar["contract"][facts.contract_type], tr["contract"][facts.contract_type]),
        ),
        (pair("start_date"), same(facts.start_date.isoformat())),
        (pair("end_date"), end),
        (pair("basic_wage"), money_pair(facts.basic_wage_aed)),
        (pair("total_wage"), money_pair(facts.total_wage_aed)),
    ]

    requests = []
    if analysis.claim:
        requests.append(pair("request_pay"))
    if analysis.violations:
        requests.append(pair("request_comply"))
    requests.append(pair("request_other"))

    return Letter(
        lang=lang,
        two_columns=lang != "ar",
        tr_dir="rtl" if lang in RTL else "ltr",
        tr_font=font_stack(lang),
        s_ar=ar,
        s_tr=tr,
        subject=subject,
        worker_rows=worker_rows,
        facts=Pair(writer.letter_facts_ar, writer.letter_facts_translation),
        legal_basis=[Pair(clause_ref(c, "ar"), clause_ref(c, "en")) for c in _cited(analysis)],
        claims=[
            ClaimRow(
                item=item,
                amount=money_pair(line.amount_aed)
                if line.amount_aed is not None
                else Pair(ar["not_calculated"], tr["not_calculated"]),
            )
            for item, line in zip(items, analysis.claim, strict=True)
        ],
        total=money_pair(analysis.total_aed) if analysis.claim else None,
        requests=requests,
        attachments=[
            Pair(a, t) for a, t in zip(ar["attachment_list"], tr["attachment_list"], strict=True)
        ],
        date=today.isoformat(),
    )


def _item(line: ClaimLine, ar: dict[str, Any], tr: dict[str, Any]) -> Pair:
    key = ITEM_KEYS.get(line.item)
    if key is None:  # a new calculator line without a translation: show it rather than drop it
        return Pair(line.item, line.item)
    return Pair(ar["item"][key], tr["item"][key])


def _cited(analysis: Analysis) -> list[str]:
    """Every clause the findings and claim lines cite, once each, in law order."""
    ids = {v.article.chunk_id for v in analysis.violations}
    ids |= {line.article.chunk_id for line in analysis.claim}

    def order(chunk_id: str) -> tuple[str, int, int]:
        law_id, art, *clause = chunk_id.split(":")
        number = int(art.removeprefix("art"))
        return law_id, number, int(clause[0].removeprefix("cl")) if clause else 0

    return sorted(ids, key=order)


@cache
def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(PDF_DIR),
        autoescape=select_autoescape(default=True, default_for_string=True),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_html(letter: Letter) -> str:
    """The letter as HTML. Fonts are referenced by file name, relative to haqqi/pdf/fonts."""
    return _env().get_template("letter.html.j2").render(letter=letter, families=FAMILIES)


def render_pdf(letter: Letter) -> bytes:
    return render_pdf_with_fonts(letter)[0]


def render_pdf_with_fonts(letter: Letter) -> tuple[bytes, list[str]]:
    """The PDF and the names of the fonts embedded in it (tests check each script's font)."""
    document = HTML(string=render_html(letter), base_url=f"{FONT_DIR}/").render()
    pdf: bytes = document.write_pdf()
    return pdf, [font.name.decode().lstrip("/") for font in document.fonts.values()]
