import re
from decimal import Decimal

import pytest

from haqqi.agents.schemas import AnalystIssue, AnalystReply
from haqqi.agents.writer import ARABIC_DIGITS, MONEY, allowed_figures, run_writer
from haqqi.config import Settings
from haqqi.core.calculator import calculate
from haqqi.llm.client import LLMClient, LLMOutputError
from haqqi.models import CaseFacts, WriterOutput
from tests.agents.fakes import FakeLLM

TC03 = CaseFacts.model_validate(
    {
        "language": "en",
        "emirate": "dubai",
        "zone": "mainland",
        "worker_type": "private_sector",
        "start_date": "2020-08-01",
        "end_date": "2026-08-31",
        "termination": "resigned",
        "notice_days_given": 30,
        "basic_wage_aed": "3500",
        "total_wage_aed": "5000",
        "issue_types": ["gratuity"],
        "story": "I worked at a hotel in Dubai for six years and resigned with proper notice. "
        "The company says my end-of-service gratuity is AED 6,000. I think this is too low.",
    }
)
GRATUITY = AnalystReply(
    issues=[
        AnalystIssue(
            issue_type="gratuity",
            finding="The worker served over five years and is owed gratuity under Art. 51.",
            chunk_ids=["fdl33-2021:art51:cl2"],
            confidence="high",
            evidence="Six years of service, resigned.",
        )
    ],
    next_steps=["Ask the employer for a written gratuity calculation.", "File with MOHRE."],
)


def writer(**overrides: object) -> WriterOutput:
    base: dict[str, object] = {
        "headline": "You may be owed more gratuity.",
        "explanation": "You worked six years. Your gratuity is [[AMOUNT_1]].",
        "amount_lines": ["Gratuity: [[AMOUNT_1]] (basic AED 3,500.00 ÷ 30 per day)"],
        "checklist": ["Keep your payslips."],
        "letter_facts_ar": "عملت لدى الشركة من 2020-08-01 حتى 2026-08-31، "
        "ومكافأة نهاية الخدمة المستحقة لي [[AMOUNT_1]].",
        "letter_facts_translation": "I worked from 2020-08-01 to 2026-08-31. "
        "My gratuity is [[AMOUNT_1]].",
    }
    return WriterOutput.model_validate(base | overrides)


def test_tokens_are_filled_with_calculator_figures() -> None:
    llm = FakeLLM({"writer": [writer()]})

    out = run_writer(llm, TC03, GRATUITY, calculate(TC03))

    assert "AED 16,056.85" in out.explanation
    assert "16,056.85 درهم" in out.letter_facts_ar
    assert "AED 16,056.85" in out.letter_facts_translation
    assert llm.stages() == ["writer"]


def test_every_aed_figure_in_the_output_is_a_calculator_figure() -> None:
    calc = calculate(TC03)
    out = run_writer(FakeLLM({"writer": [writer()]}), TC03, GRATUITY, calc)
    allowed = allowed_figures(calc)
    text = " ".join(
        [out.explanation, *out.amount_lines, out.letter_facts_ar, out.letter_facts_translation]
    )

    figures = [m.group(1) or m.group(2) for m in MONEY.finditer(text.translate(ARABIC_DIGITS))]
    assert figures
    assert all(Decimal(f.replace(",", "")) in allowed for f in figures)


@pytest.mark.parametrize(
    "bad",
    [
        {"explanation": "Your employer owes you AED 1,000,000."},
        {"letter_facts_ar": "المطالبة: ٥٠٠٠ درهم"},  # Arabic-Indic digits, not a calculator figure
        {"explanation": "Owed: [[AMOUNT_7]]"},  # unknown token
        {"letter_facts_ar": "I worked six years: [[AMOUNT_1]]"},  # no Arabic
    ],
)
def test_bad_output_gets_one_retry_then_fails(bad: dict[str, object]) -> None:
    llm = FakeLLM({"writer": [writer(**bad), writer(**bad)]})
    with pytest.raises(LLMOutputError, match="rejected after one retry"):
        run_writer(llm, TC03, GRATUITY, calculate(TC03))
    assert llm.stages() == ["writer", "writer"]


def test_a_bad_first_reply_can_be_fixed_by_the_retry() -> None:
    llm = FakeLLM({"writer": [writer(explanation="You are owed AED 6,000."), writer()]})
    out = run_writer(llm, TC03, GRATUITY, calculate(TC03))
    assert "AED 16,056.85" in out.explanation


@pytest.mark.live
def test_live_tc03_writer_letter_is_arabic_and_money_comes_from_the_calculator() -> None:
    settings = Settings()
    if not settings.k2_api_key:
        pytest.skip("K2_API_KEY not set")
    calc = calculate(TC03)

    out = run_writer(LLMClient.from_settings(settings), TC03, GRATUITY, calc)

    assert re.search(r"[؀-ۿ]", out.letter_facts_ar)
    assert "16,056.85" in " ".join(out.amount_lines)
    text = " ".join(
        [out.explanation, *out.amount_lines, out.letter_facts_ar, out.letter_facts_translation]
    )
    for m in MONEY.finditer(text.translate(ARABIC_DIGITS)):
        figure = Decimal((m.group(1) or m.group(2)).replace(",", ""))
        assert figure.quantize(Decimal("0.01")) in allowed_figures(calc)
