import json
from datetime import date
from decimal import Decimal

from haqqi.agents import messages as m
from haqqi.agents.consistency import drop_contradictions
from haqqi.agents.schemas import AnalystReply
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
