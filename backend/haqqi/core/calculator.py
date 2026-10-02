"""The only place Haqqi computes money (CLAUDE.md). Deterministic, no LLM. Task 3.2.

Rules follow docs/IMPLEMENTATION_PLAN.md flags 2-6 and are worked by hand in
tests/core/CASES.md. Every line cites a clause that exists in data/law (see `cite`).
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from functools import cache

from haqqi.models import CaseFacts, Citation, ClaimLine
from haqqi.rag.lawdata import load_chunks


@dataclass(frozen=True)
class Config:
    gratuity_min_days: int = 365  # one year of continuous service (Art. 51(2)); flag 3
    days_per_year: int = 365  # service years = service days / 365; flag 3
    gratuity_days_first_5_years: int = 21  # Art. 51(2)(a)
    gratuity_days_after_5_years: int = 30  # Art. 51(2)(b)
    gratuity_cap_months: int = 24  # two years' (basic) wage, Art. 51(6)
    days_in_month: int = 30  # daily wage = monthly wage / 30
    full_time_weekly_hours: int = 48  # part-time base, CR 1/2022 Art. 30; flag 4 (user decision)
    notice_min_days: int = 30  # Art. 43(1)
    notice_max_days: int = 90  # Art. 43(1)
    deduction_max_share: Decimal = Decimal("0.5")  # Art. 25(2)
    mohre_decision_limit_aed: Decimal = Decimal(50000)  # Art. 54(2)


CONFIG = Config()

CENT = Decimal("0.01")


@dataclass(frozen=True)
class CalcResult:
    claim: list[ClaimLine]
    worker_owes: list[ClaimLine]
    total_aed: Decimal
    above_mohre_limit: bool
    service_days: int | None = None
    notes: list[str] = field(default_factory=list)


@cache
def _quotes() -> dict[str, Citation]:
    return {
        c.id: Citation(
            chunk_id=c.id,
            law_id=c.law_id,
            article_no=c.article_no,
            clause_no=c.clause_no,
            quote=c.text_en,
        )
        for c in load_chunks()
    }


def cite(chunk_id: str) -> Citation:
    """Citation for a clause in data/law; raises KeyError for ids that don't exist."""
    return _quotes()[chunk_id]


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def aed(value: Decimal) -> str:
    return f"AED {money(value):,.2f}"


def num(value: Decimal, places: int = 4) -> str:
    return f"{value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP):,}"


def service_days(start: date, end: date, unpaid_absence_days: int = 0) -> int:
    """Both ends inclusive, minus unpaid absence (Art. 51(4)); flag 3."""
    return (end - start).days + 1 - unpaid_absence_days


def calculate(f: CaseFacts) -> CalcResult:
    claim: list[ClaimLine] = []
    owes: list[ClaimLine] = []
    notes: list[str] = []
    daily_total = f.total_wage_aed / CONFIG.days_in_month
    daily_basic = f.basic_wage_aed / CONFIG.days_in_month
    job_ended = f.termination != "still_employed"

    if f.months_unpaid:
        claim.append(
            ClaimLine(
                item="Unpaid wages",
                amount_aed=money(f.months_unpaid * f.total_wage_aed),
                formula=f"{f.months_unpaid} month(s) × {aed(f.total_wage_aed)} total monthly wage",
                article=cite("fdl33-2021:art22:cl2"),
            )
        )

    if f.deducted_amount_aed:
        claim.append(_deductions(f, notes))

    shortfall, notice_formula = _notice_shortfall(f)
    if shortfall and f.termination == "employer":
        claim.append(
            ClaimLine(
                item="Notice pay",
                amount_aed=money(shortfall * daily_total),
                formula=f"{notice_formula} × {aed(daily_total)} daily total wage "
                f"({aed(f.total_wage_aed)} ÷ 30)",
                article=cite("fdl33-2021:art43:cl3"),
            )
        )
    if shortfall and f.termination == "resigned":
        owes.append(
            ClaimLine(
                item="Notice pay you may owe your employer",
                amount_aed=money(shortfall * daily_total),
                formula=f"{notice_formula} × {aed(daily_total)} daily total wage",
                article=cite("fdl33-2021:art43:cl3"),
                note="You resigned without serving the full notice period. This is shown "
                "separately and is not subtracted from your claim.",
            )
        )

    days: int | None = None
    if job_ended:
        assert f.end_date is not None  # CaseFacts guarantees it once the job has ended
        days = service_days(f.start_date, f.end_date, f.unpaid_absence_days)
        claim.append(_gratuity(f, days, daily_basic))
        leave = _leave(f, daily_basic)
        if leave:
            claim.append(leave)

    total = sum((line.amount_aed for line in claim if line.amount_aed is not None), Decimal(0))
    return CalcResult(
        claim=claim,
        worker_owes=owes,
        total_aed=money(total),
        above_mohre_limit=total > CONFIG.mohre_decision_limit_aed,
        service_days=days,
        notes=notes,
    )


def _deductions(f: CaseFacts, notes: list[str]) -> ClaimLine:
    note = "Recoverable unless it falls under an allowed case in Art. 25."
    limit = f.total_wage_aed * CONFIG.deduction_max_share
    if f.deducted_monthly_aed is not None and f.deducted_monthly_aed > limit:
        over = (
            f"The monthly deduction ({aed(f.deducted_monthly_aed)}) is more than 50% of the wage "
            f"({aed(limit)}), which Art. 25(2) never allows."
        )
        note = f"{note} {over}"
        notes.append(over)
    return ClaimLine(
        item="Deductions from wages",
        amount_aed=money(f.deducted_amount_aed),
        formula=f"{aed(f.deducted_amount_aed)} reported as deducted",
        article=cite("fdl33-2021:art25:cl1"),
        note=note,
    )


def _notice_shortfall(f: CaseFacts) -> tuple[int, str]:
    lo, hi = CONFIG.notice_min_days, CONFIG.notice_max_days
    period = min(max(f.notice_days_contract, lo), hi)
    shortfall = max(period - f.notice_days_given, 0)
    adjusted = (
        f" (contract says {f.notice_days_contract}; the law requires {lo}–{hi})"
        if period != f.notice_days_contract
        else ""
    )
    return shortfall, (
        f"({period} days' notice{adjusted} − {f.notice_days_given} days given) = {shortfall} days"
    )


def _gratuity(f: CaseFacts, days: int, daily_basic: Decimal) -> ClaimLine:
    item = "End-of-service gratuity"
    full_time_cite = cite("fdl33-2021:art51:cl2")
    if days < CONFIG.gratuity_min_days:
        return ClaimLine(
            item=item,
            amount_aed=Decimal("0.00"),
            formula=f"{days} service days is less than one year ({CONFIG.gratuity_min_days} days)",
            article=full_time_cite,
            note="Gratuity starts after one year of continuous service.",
        )
    if f.contract_type == "flexible":
        return ClaimLine(
            item=item,
            amount_aed=None,
            formula="Not calculated for flexible contracts",
            article=cite("fdl33-2021:art52"),
            note="Ask MOHRE (80084) how gratuity applies to your contract.",
        )
    if f.contract_type == "part_time" and f.weekly_hours is None:
        return ClaimLine(
            item=item,
            amount_aed=None,
            formula="Not calculated: weekly contract hours unknown",
            article=cite("cr1-2022:art30:cl1"),
            note="Part-time gratuity depends on your contract hours. Ask MOHRE (80084).",
        )

    years = Decimal(days) / CONFIG.days_per_year
    first = min(years, Decimal(5))
    rest = max(years - 5, Decimal(0))
    wage_days = (
        first * CONFIG.gratuity_days_first_5_years + rest * CONFIG.gratuity_days_after_5_years
    )
    amount = wage_days * daily_basic
    cap = f.basic_wage_aed * CONFIG.gratuity_cap_months
    formula = (
        f"{days:,} service days ÷ 365 = {num(years)} years; "
        f"{num(first)} × {CONFIG.gratuity_days_first_5_years} + "
        f"{num(rest)} × {CONFIG.gratuity_days_after_5_years} = {num(wage_days)} days × "
        f"{aed(daily_basic)} daily basic wage ({aed(f.basic_wage_aed)} ÷ 30) = {aed(amount)}"
    )
    if amount > cap:
        amount = cap
        formula += f"; capped at 2 years' basic wage (24 × {aed(f.basic_wage_aed)}) = {aed(cap)}"
    article = full_time_cite
    if f.contract_type == "part_time":
        assert f.weekly_hours is not None
        hours = CONFIG.full_time_weekly_hours
        amount = amount * f.weekly_hours / hours
        formula += f"; part-time: × {num(f.weekly_hours, 2)} h ÷ {hours} h a week = {aed(amount)}"
        article = cite("cr1-2022:art30:cl1")
    return ClaimLine(item=item, amount_aed=money(amount), formula=formula, article=article)


def _leave(f: CaseFacts, daily_basic: Decimal) -> ClaimLine | None:
    item = "Unused annual leave"
    if f.unused_leave_days is None:
        if "leave" not in f.issue_types:
            return None
        return ClaimLine(
            item=item,
            amount_aed=None,
            formula="Not calculated: number of unused leave days unknown",
            article=cite("fdl33-2021:art29:cl9"),
            note="Count your unused leave days (payslips or leave records) and add them.",
        )
    if f.unused_leave_days == 0:
        return None
    return ClaimLine(
        item=item,
        amount_aed=money(f.unused_leave_days * daily_basic),
        formula=f"{f.unused_leave_days} days × {aed(daily_basic)} daily basic wage "
        f"({aed(f.basic_wage_aed)} ÷ 30)",
        article=cite("fdl33-2021:art29:cl9"),
    )
