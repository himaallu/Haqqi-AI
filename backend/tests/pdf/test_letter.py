"""Complaint letter (tasks 5.2, 5.3): golden HTML, money only from the calculator, catalogs."""

import io
import json
import os
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pypdf import PdfReader

from haqqi.agents.writer import fill_and_check
from haqqi.core.calculator import calculate, cite
from haqqi.models import Analysis, CaseFacts, Violation
from haqqi.pdf.letter import (
    ITEM_KEYS,
    STRINGS_DIR,
    Identity,
    LetterError,
    build_letter,
    render_html,
    render_pdf,
    render_pdf_with_fonts,
)
from tests.agents.test_writer import TC03, writer

GOLDEN = Path(__file__).parent / "golden"
TODAY = date(2026, 10, 3)
FACTS_AR = (
    "عملت في فندق بدبي من 2020-08-01 حتى 2026-08-31، واستقلت بعد أن قدمت إشعاراً مدته 30 يوماً.\n"
    "عرضت عليّ الشركة مكافأة نهاية خدمة أقل من المستحق قانوناً."
)
FACTS_TR = (
    "I worked at a hotel in Dubai from 2020-08-01 to 2026-08-31 "
    "and resigned with 30 days' notice.\n"
    "The company offered me less gratuity than the law requires."
)
MONEY_FIGURE = re.compile(r"\d{1,3}(?:,\d{3})*\.\d{2}")


def analysis_for(facts: CaseFacts) -> Analysis:
    calc = calculate(facts)
    out = fill_and_check(writer(letter_facts_ar=FACTS_AR, letter_facts_translation=FACTS_TR), calc)
    return Analysis(
        in_scope=True,
        violations=[
            Violation(
                issue="Gratuity offered is below Art. 51",
                article=cite("fdl33-2021:art51:cl2"),
                confidence="high",
            )
        ],
        claim=calc.claim,
        total_aed=calc.total_aed,
        writer=out,
    )


def tc03(lang: str) -> CaseFacts:
    return TC03.model_copy(update={"language": lang})


@pytest.mark.parametrize("lang", ["en", "ur", "ar"])
def test_letter_html_matches_golden(lang: str) -> None:
    facts = tc03(lang)
    letter = build_letter(facts, analysis_for(facts), Identity(employer="Example Hotel"), TODAY)
    html = render_html(letter)
    path = GOLDEN / f"tc03_{lang}.html"
    if os.environ.get("UPDATE_GOLDEN") == "1":
        path.parent.mkdir(exist_ok=True)
        path.write_text(html, encoding="utf-8")
    assert html == path.read_text(encoding="utf-8"), "letter changed: review, then UPDATE_GOLDEN=1"


def test_every_money_figure_in_the_pdf_is_a_claim_amount_total_or_wage() -> None:
    facts = TC03.model_copy(
        update={
            "language": "hi",
            "termination": "employer",
            "notice_days_given": 0,
            "months_unpaid": 2,
            "unused_leave_days": 12,
        }
    )
    analysis = analysis_for(facts)
    pdf = render_pdf(build_letter(facts, analysis, Identity(), TODAY))
    text = "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)

    claim = {line.amount_aed for line in analysis.claim if line.amount_aed is not None}
    allowed = claim | {analysis.total_aed, facts.basic_wage_aed, facts.total_wage_aed}
    found = {Decimal(m.replace(",", "")) for m in MONEY_FIGURE.findall(text)}
    assert found <= allowed
    assert claim | {analysis.total_aed} <= found  # every claim line and the total are printed
    assert len(claim) == 4  # unpaid wages, notice pay, gratuity, leave


def test_identity_fields_are_printed_and_blank_ones_left_to_fill_by_hand() -> None:
    facts = tc03("en")
    html = render_html(
        build_letter(facts, analysis_for(facts), Identity(name="Joel <b>S</b>"), TODAY)
    )
    assert "Joel &lt;b&gt;S&lt;/b&gt;" in html  # escaped, never markup
    assert "." * 40 in html  # labour card and employer left blank


def test_legal_basis_lists_each_cited_clause_once_in_arabic() -> None:
    facts = tc03("en")
    letter = build_letter(facts, analysis_for(facts), Identity(), TODAY)
    assert [p.ar for p in letter.legal_basis] == [
        "المادة (51) البند (2) من المرسوم بقانون اتحادي رقم (33) لسنة 2021"
    ]


def test_arabic_case_has_one_column() -> None:
    facts = tc03("ar")
    letter = build_letter(facts, analysis_for(facts), Identity(), TODAY)
    assert not letter.two_columns
    assert 'class="tr"' not in render_html(letter)


@pytest.mark.parametrize(
    "change",
    [
        {"in_scope": False},
        {"violations": [], "claim": []},
        {"writer": None},
    ],
)
def test_no_letter_without_findings_or_writer_text(change: dict[str, object]) -> None:
    facts = tc03("en")
    analysis = analysis_for(facts).model_copy(update=change)
    with pytest.raises(LetterError):
        build_letter(facts, analysis, Identity(), TODAY)


def test_every_calculator_item_has_a_translation() -> None:
    facts = TC03.model_copy(
        update={
            "termination": "employer",
            "notice_days_given": 0,
            "months_unpaid": 1,
            "deducted_amount_aed": Decimal(100),
            "unused_leave_days": 5,
        }
    )
    items = {line.item for line in calculate(facts).claim}
    assert items == set(ITEM_KEYS)


def test_catalogs_have_the_same_keys() -> None:
    def keys(data: object, prefix: str = "") -> set[str]:
        if isinstance(data, dict):
            return {k for key, v in data.items() for k in keys(v, f"{prefix}{key}.")} | {prefix}
        return {prefix}

    en = json.loads((STRINGS_DIR / "en.json").read_text(encoding="utf-8"))
    for path in STRINGS_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert keys(data) == keys(en), path.name
        assert len(data["attachment_list"]) == len(en["attachment_list"]), path.name


@pytest.mark.parametrize(
    ("lang", "font"),
    [
        ("ur", "Noto-Nastaliq-Urdu"),
        ("hi", "Noto-Sans-Devanagari"),
        ("ne", "Noto-Sans-Devanagari"),
        ("ml", "Noto-Sans-Malayalam"),
        ("bn", "Noto-Sans-Bengali"),
        ("en", "Noto-Sans"),
    ],
)
def test_translation_column_embeds_its_script_font(lang: str, font: str) -> None:
    facts = tc03(lang)
    _pdf, fonts = render_pdf_with_fonts(build_letter(facts, analysis_for(facts), Identity(), TODAY))
    assert any(name.split("+")[-1].startswith(font) for name in fonts), fonts
    assert any("Noto-Naskh-Arabic" in name for name in fonts)


@pytest.mark.parametrize("lang", ["en", "hi", "ur", "ml", "bn", "tl", "ne", "ar"])
def test_footer_disclaimer_with_mohre_80084_in_both_columns(lang: str) -> None:
    facts = tc03(lang)
    html = render_html(build_letter(facts, analysis_for(facts), Identity(), TODAY))
    assert html.count("80084") == (1 if lang == "ar" else 2)  # Arabic, plus the translation


def test_footer_disclaimer_is_in_the_pdf_text() -> None:
    facts = tc03("en")
    pdf = render_pdf(build_letter(facts, analysis_for(facts), Identity(), TODAY))
    text = "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)
    assert "not legal advice" in text and "80084" in text
