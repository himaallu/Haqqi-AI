"""Calculator tests. Every expected figure is worked by hand in tests/core/CASES.md."""

from decimal import Decimal

import pytest

from haqqi.core.calculator import CalcResult, calculate, cite, service_days
from haqqi.models import CaseFacts
from haqqi.rag.lawdata import load_chunks


def facts(**overrides: object) -> CaseFacts:
    base: dict[str, object] = {
        "language": "en",
        "emirate": "dubai",
        "zone": "mainland",
        "worker_type": "private_sector",
        "start_date": "2025-01-01",
        "basic_wage_aed": "3000",
        "total_wage_aed": "3000",
        "termination": "still_employed",
    }
    return CaseFacts.model_validate(base | overrides)


def amounts(result: CalcResult) -> dict[str, Decimal | None]:
    return {line.item: line.amount_aed for line in result.claim}


def gratuity(result: CalcResult) -> Decimal | None:
    return amounts(result)["End-of-service gratuity"]


def test_tc01_still_employed_three_months_unpaid() -> None:
    r = calculate(
        facts(
            start_date="2023-02-01", basic_wage_aed="1200", total_wage_aed="1800", months_unpaid=3
        )
    )
    assert amounts(r) == {"Unpaid wages": Decimal("5400.00")}
    assert r.total_aed == Decimal("5400.00")
    assert r.service_days is None  # no gratuity while employed


def test_tc03_resigned_after_six_years() -> None:
    r = calculate(
        facts(
            start_date="2020-08-01",
            end_date="2026-08-31",
            termination="resigned",
            basic_wage_aed="3500",
            total_wage_aed="5000",
            notice_days_given=30,
        )
    )
    assert r.service_days == 2222
    assert amounts(r) == {"End-of-service gratuity": Decimal("16056.85")}
    assert r.worker_owes == []
    assert r.total_aed == Decimal("16056.85")


def test_tc02_terminated_without_notice() -> None:
    r = calculate(
        facts(
            start_date="2024-06-01",
            end_date="2026-09-20",
            termination="employer",
            basic_wage_aed="2000",
            total_wage_aed="3000",
        )
    )
    assert amounts(r) == {
        "Notice pay": Decimal("3000.00"),
        "End-of-service gratuity": Decimal("3229.59"),
    }
    assert r.total_aed == Decimal("6229.59")


def test_tc19_under_one_year_gets_notice_but_no_gratuity() -> None:
    r = calculate(
        facts(
            start_date="2026-01-05",
            end_date="2026-09-10",
            termination="employer",
            basic_wage_aed="3000",
            total_wage_aed="4500",
        )
    )
    assert amounts(r) == {
        "Notice pay": Decimal("4500.00"),
        "End-of-service gratuity": Decimal("0.00"),
    }
    assert r.total_aed == Decimal("4500.00")


def test_tc20_gratuity_cap_and_ninety_day_notice() -> None:
    r = calculate(
        facts(
            start_date="1998-01-01",
            end_date="2026-08-31",
            termination="employer",
            basic_wage_aed="20000",
            total_wage_aed="30000",
            notice_days_contract=90,
            months_unpaid=1,
        )
    )
    assert amounts(r) == {
        "Unpaid wages": Decimal("30000.00"),
        "Notice pay": Decimal("90000.00"),
        "End-of-service gratuity": Decimal("480000.00"),
    }
    grat = next(line for line in r.claim if line.item == "End-of-service gratuity")
    assert "capped" in grat.formula
    assert r.total_aed == Decimal("600000.00")
    assert r.above_mohre_limit


def test_tc21_resigned_with_notice_salary_and_gratuity_unpaid() -> None:
    r = calculate(
        facts(
            start_date="2022-03-01",
            end_date="2026-07-31",
            termination="resigned",
            basic_wage_aed="4000",
            total_wage_aed="6000",
            notice_days_given=30,
            months_unpaid=1,
        )
    )
    assert amounts(r) == {
        "Unpaid wages": Decimal("6000.00"),
        "End-of-service gratuity": Decimal("12381.37"),
    }
    assert r.total_aed == Decimal("18381.37")
    assert not r.above_mohre_limit


def test_tc22_still_employed_leave_refused_has_no_money() -> None:
    r = calculate(
        facts(
            start_date="2022-01-01",
            basic_wage_aed="5000",
            total_wage_aed="7000",
            issue_types=["leave"],
        )
    )
    assert r.claim == []
    assert r.total_aed == Decimal("0.00")


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        ("2025-01-01", "2025-12-31", Decimal("2100.00")),  # exactly one year: 365 days
        ("2025-01-02", "2025-12-31", Decimal("0.00")),  # one day short
        ("2021-01-01", "2025-12-30", Decimal("10500.00")),  # exactly 5 × 365 days
        ("2021-01-01", "2025-12-31", Decimal("10508.22")),  # 5 calendar years incl. a leap day
    ],
)
def test_gratuity_year_boundaries(start: str, end: str, expected: Decimal) -> None:
    r = calculate(
        facts(start_date=start, end_date=end, termination="resigned", notice_days_given=30)
    )
    assert gratuity(r) == expected


def test_part_time_gratuity_is_prorated_against_48_hours() -> None:
    r = calculate(
        facts(
            start_date="2020-08-01",
            end_date="2026-08-31",
            termination="resigned",
            notice_days_given=30,
            basic_wage_aed="3500",
            total_wage_aed="5000",
            contract_type="part_time",
            weekly_hours="24",
        )
    )
    line = r.claim[0]
    assert line.amount_aed == Decimal("8028.42")
    assert "÷ 48 h" in line.formula
    assert line.article.chunk_id == "cr1-2022:art30:cl1"


def test_part_time_without_hours_and_flexible_are_not_calculated() -> None:
    ended = {"start_date": "2020-01-01", "end_date": "2023-01-01", "termination": "employer"}
    for contract in (
        {"contract_type": "part_time"},
        {"contract_type": "flexible"},
    ):
        r = calculate(facts(**ended, **contract, notice_days_given=30))
        assert gratuity(r) is None
        assert "Not calculated" in r.claim[0].formula
        assert r.total_aed == Decimal("0.00")


def test_unpaid_absence_days_reduce_service() -> None:
    r = calculate(
        facts(
            start_date="2025-01-01",
            end_date="2026-01-20",
            termination="resigned",
            notice_days_given=30,
            unpaid_absence_days=30,
        )
    )
    assert r.service_days == 355
    assert gratuity(r) == Decimal("0.00")


@pytest.mark.parametrize(("contract_days", "expected_days"), [(14, 30), (60, 60), (120, 90)])
def test_notice_period_is_clamped_to_the_legal_range(
    contract_days: int, expected_days: int
) -> None:
    r = calculate(
        facts(
            start_date="2026-01-01",
            end_date="2026-06-30",
            termination="employer",
            notice_days_contract=contract_days,
        )
    )
    assert amounts(r)["Notice pay"] == Decimal(expected_days * 100).quantize(Decimal("0.01"))


def test_resigning_without_notice_is_shown_separately_not_subtracted() -> None:
    r = calculate(
        facts(
            start_date="2026-01-01",
            end_date="2026-06-30",
            termination="resigned",
            notice_days_given=10,
            months_unpaid=1,
        )
    )
    assert [(line.item, line.amount_aed) for line in r.worker_owes] == [
        ("Notice pay you may owe your employer", Decimal("2000.00"))
    ]
    assert r.total_aed == Decimal("3000.00")  # the unpaid month only


def test_deductions_refund_and_fifty_percent_note() -> None:
    tc04 = calculate(
        facts(total_wage_aed="3000", deducted_amount_aed="2400", deducted_monthly_aed="600")
    )
    assert amounts(tc04) == {"Deductions from wages": Decimal("2400.00")}
    assert tc04.notes == []

    heavy = calculate(
        facts(total_wage_aed="3000", deducted_amount_aed="1800", deducted_monthly_aed="1800")
    )
    assert "50%" in heavy.claim[0].note
    assert heavy.notes


def test_leave_is_paid_at_the_end_or_marked_not_calculated() -> None:
    ended = {"start_date": "2026-01-01", "end_date": "2026-06-30", "termination": "employer"}
    known = calculate(facts(**ended, notice_days_given=30, unused_leave_days=12))
    assert amounts(known)["Unused annual leave"] == Decimal("1200.00")

    unknown = calculate(facts(**ended, notice_days_given=30, issue_types=["leave"]))
    assert amounts(unknown)["Unused annual leave"] is None

    not_raised = calculate(facts(**ended, notice_days_given=30))
    assert "Unused annual leave" not in amounts(not_raised)


def test_every_line_cites_a_real_clause_and_shows_its_formula() -> None:
    known = {c.id for c in load_chunks()}
    r = calculate(
        facts(
            start_date="2020-01-01",
            end_date="2026-01-01",
            termination="employer",
            months_unpaid=2,
            deducted_amount_aed="500",
            unused_leave_days=5,
        )
    )
    assert len(r.claim) == 5
    for line in r.claim:
        assert line.article.chunk_id in known
        assert line.article.quote
        assert line.formula


def test_cite_rejects_unknown_ids() -> None:
    with pytest.raises(KeyError):
        cite("fdl33-2021:art999:cl1")


def test_service_days_counts_both_ends() -> None:
    from datetime import date

    assert service_days(date(2025, 1, 1), date(2025, 1, 1)) == 1
    assert service_days(date(2025, 1, 1), date(2025, 12, 31), unpaid_absence_days=5) == 360


def test_gratuity_formula_shows_the_30_day_rate_only_after_five_years() -> None:
    def formula(start: str, end: str) -> str:
        r = calculate(facts(start_date=start, end_date=end, termination="employer"))
        return next(line.formula for line in r.claim if line.item == "End-of-service gratuity")

    assert "× 30 " not in formula("2024-06-01", "2026-09-20")  # TC-02: 2.3 years
    assert "× 21 + " in formula("2020-08-01", "2026-08-31")  # TC-03: 6.1 years
