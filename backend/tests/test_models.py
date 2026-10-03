from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from haqqi.models import Analysis, CaseFacts, Citation, ClaimLine, Emirate, ExtractedFacts


def facts(**overrides: object) -> CaseFacts:
    base: dict[str, object] = {
        "language": "hi",
        "emirate": "ajman",
        "zone": "mainland",
        "worker_type": "private_sector",
        "start_date": "2023-02-01",
        "basic_wage_aed": "1200",
        "total_wage_aed": "1800",
        "termination": "still_employed",
        "months_unpaid": 3,
    }
    return CaseFacts.model_validate(base | overrides)


def test_case_facts_round_trip_keeps_decimals_and_dates() -> None:
    original = facts()

    again = CaseFacts.model_validate_json(original.model_dump_json())

    assert again == original
    assert again.basic_wage_aed == Decimal("1200")
    assert again.emirate is Emirate.AJMAN
    assert again.start_date == date(2023, 2, 1)
    assert again.notice_days_contract == 30


def test_extracted_facts_are_all_optional() -> None:
    extracted = ExtractedFacts()
    assert extracted.basic_wage_aed is None
    assert extracted.issue_types == []


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"basic_wage_aed": "2000"}, "basic wage cannot exceed total"),
        ({"termination": "resigned"}, "end_date is required"),
        ({"end_date": "2025-01-01"}, "must be empty while still employed"),
        ({"termination": "employer", "end_date": "2020-01-01"}, "before start_date"),
        ({"total_wage_aed": "-5"}, "greater than 0"),
        ({"surprise": 1}, "Extra inputs"),
    ],
)
def test_case_facts_rejects_inconsistent_input(overrides: dict[str, object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        facts(**overrides)


def test_analysis_round_trip() -> None:
    cite = Citation(
        chunk_id="fdl33-2021:art22:cl2", law_id="fdl33-2021", article_no=22, clause_no=2, quote="…"
    )
    line = ClaimLine(
        item="Unpaid wages", amount_aed=Decimal("5400.00"), formula="3 × 1,800", article=cite
    )
    analysis = Analysis(in_scope=True, claim=[line], total_aed=Decimal("5400.00"))

    assert Analysis.model_validate_json(analysis.model_dump_json()) == analysis


def test_analysis_saved_before_the_facts_only_writer_still_loads() -> None:
    old_writer = {
        "headline": "h",
        "explanation": "e",
        "amount_lines": [],
        "checklist": [],
        "arabic_letter": "إلى الوزارة",
        "letter_translation": "To MOHRE",
    }
    analysis = Analysis.model_validate({"in_scope": True, "writer": old_writer})
    assert analysis.writer is not None
    assert analysis.writer.explanation == "e"
    assert analysis.writer.letter_facts_ar == ""  # the complaint download asks for a new analysis
