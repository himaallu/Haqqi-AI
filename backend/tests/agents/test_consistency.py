import json
from datetime import date
from decimal import Decimal

import pytest

from haqqi.agents import messages as m
from haqqi.agents.consistency import drop_contradictions, drop_ruled_out_notice
from haqqi.agents.schemas import AnalystIssue, AnalystReply
from haqqi.core.calculator import calculate
from haqqi.models import CaseFacts

# TC-02: 842 days of service, gratuity 3,229.59 (tests/core/CASES.md)
TC02 = CaseFacts.model_validate(
    {
        "language": "ur",
        "emirate": "abu_dhabi",
        "zone": "mainland",
        "worker_type": "private_sector",
        "start_date": "2024-06-01",
        "end_date": "2026-09-20",
        "termination": "employer",
        "basic_wage_aed": "2000",
        "total_wage_aed": "3000",
        "issue_types": ["termination", "notice_pay"],
        "story": "Terminated the same day without notice.",
    }
)
# What the Analyst wrote on 4 Oct (language check, TC-02).
SEEN = (
    "The worker is not entitled to end-of-service gratuity because they have not completed "
    "one year of continuous service as required by fdl33-2021:art51:cl2."
)


def test_a_note_denying_a_calculated_gratuity_is_dropped() -> None:
    calc = calculate(TC02)
    assert calc.total_aed == Decimal("6229.59")
    other = "Visa fines are not covered by the law provided."
    reply = AnalystReply(issues=[], not_covered=[SEEN, other])

    kept = drop_contradictions(reply, calc).not_covered
    assert kept == [other]


def test_the_same_note_stays_when_the_calculator_paid_no_gratuity() -> None:
    short = TC02.model_copy(update={"start_date": date(2026, 1, 1)})  # 263 days
    calc = calculate(short)
    gratuity = next(line for line in calc.claim if line.item == "End-of-service gratuity")
    assert gratuity.amount_aed == Decimal("0.00")
    reply = AnalystReply(issues=[], not_covered=[SEEN])
    assert drop_contradictions(reply, calc).not_covered == [SEEN]


def test_agents_get_the_service_length_counted_by_code() -> None:
    calc = calculate(TC02)
    for msgs in (
        m.analyst_messages(TC02, [], calc),
        m.critic_messages(TC02, [], calc, AnalystReply(issues=[])),
        m.writer_messages(TC02, AnalystReply(issues=[]), calc),
    ):
        user = msgs[1].content
        block = user.split("SERVICE:\n", 1)[1].split("\n\n", 1)[0]
        assert json.loads(block) == {
            "job_ended": True,
            "service_days": 842,
            "service_years": 2.31,
            "at_least_one_year": True,
        }


def test_still_employed_has_no_service_count() -> None:
    employed = TC02.model_copy(update={"end_date": None, "termination": "still_employed"})
    user = m.analyst_messages(employed, [], calculate(employed))[1].content
    assert '"job_ended": false' in user


# N-18-like: dismissed on 31 Aug 2026 with the full 30 days' notice (eval, 5 Oct).
NOTICE_SERVED = TC02.model_copy(
    update={
        "start_date": date(2025, 6, 1),
        "end_date": date(2026, 8, 31),
        "notice_days_contract": 30,
        "notice_days_given": 30,
    }
)


def finding(issue_type: str, *chunk_ids: str) -> AnalystIssue:
    return AnalystIssue(
        issue_type=issue_type,
        finding="…",
        chunk_ids=list(chunk_ids),
        confidence="medium",
        evidence="…",
    )


def test_notice_findings_are_dropped_when_the_full_notice_was_served() -> None:
    reply = AnalystReply(
        issues=[
            finding("notice_pay", "fdl33-2021:art43:cl1", "fdl33-2021:art43:cl3"),
            finding("termination", "fdl33-2021:art43:cl1", "fdl33-2021:art47:cl1"),
            finding("gratuity", "fdl33-2021:art51:cl2"),
        ]
    )
    kept = drop_ruled_out_notice(reply, NOTICE_SERVED).issues
    assert [i.chunk_ids for i in kept] == [["fdl33-2021:art47:cl1"], ["fdl33-2021:art51:cl2"]]


@pytest.mark.parametrize(
    "change",
    [
        {"notice_days_given": 0},  # no notice: a real breach
        {"notice_days_contract": 20, "notice_days_given": 20},  # the law requires 30: 10 days short
        {"termination": "still_employed", "end_date": None},
    ],
)
def test_notice_findings_are_kept_unless_the_full_notice_was_served(
    change: dict[str, object],
) -> None:
    reply = AnalystReply(issues=[finding("notice_pay", "fdl33-2021:art43:cl1")])
    facts = NOTICE_SERVED.model_copy(update=change)
    assert drop_ruled_out_notice(reply, facts) == reply


def test_pre_2022_contracts_use_the_contract_notice_too() -> None:
    # Your decision (5 Oct, N-12): the contract notice applies, not Art. 65(6)'s by service length.
    reply = AnalystReply(
        issues=[
            finding("notice_pay", "fdl33-2021:art65:cl6", "fdl33-2021:art43:cl3"),
            finding("gratuity", "fdl33-2021:art51:cl2"),
        ]
    )
    facts = NOTICE_SERVED.model_copy(update={"start_date": date(2001, 6, 1)})
    kept = drop_ruled_out_notice(reply, facts).issues
    assert [i.chunk_ids for i in kept] == [["fdl33-2021:art51:cl2"]]
