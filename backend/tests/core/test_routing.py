"""Routing table test on the n8n harness cases (legacy/n8n/"Haqqi Test.json").

Each row gives the form answers ("not sure" = None) and what the Intake agent would extract
from the story; the live Intake test (task 3.7) checks the extraction itself.
"""

import pytest

from haqqi.core.routing import MISSING_START, MISSING_WAGE, route_case
from haqqi.models import ExtractedFacts, WorkerType, Zone

WAGES = {"basic_wage_aed": "1800", "total_wage_aed": "2400", "start_date": "2024-01-01"}


@pytest.mark.parametrize(
    ("case", "form_zone", "form_worker", "extracted", "route", "referral", "missing"),
    [
        # TC-01: mainland company, full facts
        ("TC-01", "mainland", "private_sector", WAGES, "ready", None, []),
        # TC-07: form "Not sure"; story says the company is registered in DIFC
        ("TC-07", None, None, {**WAGES, "zone": "difc"}, "out_of_scope", "difc_adgm", []),
        # TC-08: form says a household (domestic work)
        ("TC-08", None, "domestic", WAGES, "out_of_scope", "domestic", []),
        # TC-09: no salary, no start date
        (
            "TC-09",
            "mainland",
            "private_sector",
            {},
            "need_info",
            None,
            [MISSING_WAGE, MISSING_START],
        ),
        # TC-14: form says free zone; injected contract text made the model say mainland
        (
            "TC-14",
            "free_zone",
            "private_sector",
            {**WAGES, "zone": "mainland", "in_scope": True},
            "out_of_scope",
            "free_zone",
            [],
        ),
        # TC-15: form "Not sure"; story: a nanny living with the sponsoring family
        ("TC-15", None, None, {**WAGES, "worker_type": "domestic"}, "out_of_scope", "domestic", []),
        # TC-16: salary given, start date missing
        (
            "TC-16",
            "mainland",
            "private_sector",
            {"basic_wage_aed": "1800", "total_wage_aed": "2400"},
            "need_info",
            None,
            [MISSING_START],
        ),
        # TC-17: dates given, salary missing
        (
            "TC-17",
            "mainland",
            "private_sector",
            {"start_date": "2023-06-01", "end_date": "2026-09-18"},
            "need_info",
            None,
            [MISSING_WAGE],
        ),
    ],
)
def test_route_harness_cases(
    case: str,
    form_zone: Zone | None,
    form_worker: WorkerType | None,
    extracted: dict[str, object],
    route: str,
    referral: str | None,
    missing: list[str],
) -> None:
    decision = route_case(ExtractedFacts.model_validate(extracted), form_zone, form_worker)

    assert (decision.route, decision.referral, decision.missing) == (route, referral, missing), case


def test_form_answer_beats_the_model_in_both_directions() -> None:
    model_says_free_zone = ExtractedFacts.model_validate({**WAGES, "zone": "free_zone"})
    assert route_case(model_says_free_zone, form_zone="mainland").route == "ready"

    model_says_mainland = ExtractedFacts.model_validate({**WAGES, "zone": "mainland"})
    assert route_case(model_says_mainland, form_zone="adgm").referral == "difc_adgm"


def test_one_wage_figure_is_enough() -> None:
    only_total = ExtractedFacts.model_validate(
        {"total_wage_aed": "2000", "start_date": "2024-01-01"}
    )
    assert route_case(only_total, "mainland").route == "ready"


@pytest.mark.parametrize(
    ("form_zone", "form_worker", "kind"),
    [(None, "domestic", "domestic"), ("difc", None, "difc_adgm"), ("free_zone", None, "free_zone")],
)
def test_referral_texts_include_the_mohre_number(
    form_zone: Zone | None, form_worker: WorkerType | None, kind: str
) -> None:
    decision = route_case(ExtractedFacts.model_validate(WAGES), form_zone, form_worker)

    assert decision.referral == kind
    assert decision.referral_text and "80084" in decision.referral_text
