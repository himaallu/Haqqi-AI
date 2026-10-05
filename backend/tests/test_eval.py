"""The evaluation set and metric definitions (Sprint 7)."""

from decimal import Decimal
from typing import Any

from eval.metrics import p95, summarize, table
from eval.offline import calculator_failures
from eval.run_eval import contains_amount
from eval.validate import problems


def test_the_case_file_is_valid_and_has_50_cases() -> None:
    errors, cases = problems()
    assert errors == []
    assert len(cases) == 50


def test_calculator_matches_every_hand_worked_case() -> None:
    checked, failures = calculator_failures()
    assert checked == 40 and failures == []


def test_injected_amounts_are_found_in_any_digit_style() -> None:
    million = Decimal("1000000")
    assert contains_amount("You are owed AED 1,000,000 in compensation", million)
    assert contains_amount("المبلغ ١٬٠٠٠٬٠٠٠ درهم", million)
    assert not contains_amount("Unpaid wages: AED 5,000.00", million)
    assert not contains_amount("AED 10000000", million)  # a different number


def test_p95_is_nearest_rank() -> None:
    assert p95([]) is None
    assert p95([10.0]) == 10.0
    assert p95([float(n) for n in range(1, 21)]) == 19.0


def test_summary_uses_only_the_cases_each_metric_applies_to() -> None:
    results: list[dict[str, Any]] = [
        {
            "outcome_ok": True,
            "issue_recall": 1.0,
            "analysed": True,
            "hit_at_5": True,
            "violation_cited": [True, True],
            "violation_supported": [True, False],
            "calculator_exact": True,
            "seconds": 30.0,
            "seeded": True,
            "critic_caught": True,
        },
        {
            "outcome_ok": False,
            "issue_recall": 0.5,
            "analysed": True,
            "hit_at_5": False,
            "violation_cited": [True],
            "violation_supported": [True],
            "calculator_exact": True,
            "seconds": 60.0,
            "injected": True,
            "injection_resisted": True,
        },
        {"outcome_ok": True, "issue_recall": None},  # a referral: no analysis
        {"error": "LLMUnavailable: down"},
    ]
    m = summarize(results)
    assert m["outcome_accuracy"] == round(2 / 3, 3)
    assert m["issue_detection"] == 0.75
    assert m["retrieval_hit_at_5"] == 0.5
    assert m["citations_cited"] == 1.0
    assert m["citations_supported"] == round(2 / 3, 3)
    assert m["critic_catch_rate"] == 1.0
    assert m["calculator_correctness"] == 1.0
    assert m["injection_resistance"] == 1.0
    assert m["latency_p95_s"] == 60.0
    assert m["errors"] == 1
    assert "| outcome accuracy | 67% | >= 95% |" in table(m)


def test_latency_is_also_reported_per_provider() -> None:
    def analysed(seconds: float, provider: str | None) -> dict[str, Any]:
        result: dict[str, Any] = {
            "outcome_ok": True,
            "analysed": True,
            "calculator_exact": True,
            "seconds": seconds,
        }
        if provider:
            result["provider"] = provider
        return result

    results = [
        analysed(20, "gemini"),
        analysed(30, "gemini"),
        analysed(200, "k2"),
        analysed(250, None),
    ]
    by_provider = summarize(results)["latency_p95_by_provider"]
    assert by_provider == {"gemini": 30, "k2": 250}  # untagged results are the older K2 runs
