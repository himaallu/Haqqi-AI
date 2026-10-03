from datetime import date
from decimal import Decimal

import pytest

from haqqi.agents.intake import run_intake
from haqqi.api.schemas import CreateCaseRequest
from haqqi.config import Settings
from haqqi.llm.client import LLMClient
from haqqi.models import ExtractedFacts
from tests.agents.fakes import FakeLLM


def test_form_answers_override_the_model_and_language_comes_from_the_form() -> None:
    model_says = ExtractedFacts(zone="mainland", total_wage_aed=Decimal(900), issue_types=[])
    llm = FakeLLM({"intake": [model_says]})
    req = CreateCaseRequest(
        language="ur",
        story="JAFZA company, salary late",
        zone="free_zone",
        total_wage_aed=Decimal(4000),
    )

    facts = run_intake(llm, req)

    assert facts.zone == "free_zone"
    assert facts.total_wage_aed == Decimal(4000)
    assert facts.language == "ur"
    assert facts.issue_types == ["other"]
    assert llm.stages() == ["intake"]


TC01 = (
    "मैं अजमान में एक कंस्ट्रक्शन कंपनी में हेल्पर का काम करता हूँ। पिछले 3 महीने से मेरी तनख्वाह नहीं मिली "
    "है। कंपनी हर बार बोलती है अगले महीने देंगे। मैं अभी भी वहीं काम कर रहा हूँ।"
)
TC18 = (
    "I started as a cleaner in Ajman on 1 May 2025. My total salary is AED 2,200 a month and my "
    "basic is AED 1,600. My August salary has not been paid. I still work there."
)


def live_client() -> LLMClient:
    settings = Settings()
    if not settings.k2_api_key:
        pytest.skip("K2_API_KEY not set")
    return LLMClient.from_settings(settings)


@pytest.mark.live
def test_live_tc01_hindi_unpaid_wages() -> None:
    req = CreateCaseRequest(
        language="hi",
        story=TC01,
        emirate="ajman",
        zone="mainland",
        worker_type="private_sector",
        basic_wage_aed=Decimal(1200),
        total_wage_aed=Decimal(1800),
        start_date=date(2023, 2, 1),
    )
    facts = run_intake(live_client(), req)

    assert "unpaid_wages" in facts.issue_types
    assert facts.total_wage_aed == Decimal(1800)
    assert facts.months_unpaid == 3
    assert facts.termination == "still_employed"


@pytest.mark.live
def test_live_tc18_fills_dates_and_wages_from_the_story() -> None:
    req = CreateCaseRequest(language="en", story=TC18, emirate="ajman", zone="mainland")
    facts = run_intake(live_client(), req)

    assert facts.start_date == date(2025, 5, 1)
    assert facts.total_wage_aed == Decimal(2200)
    assert facts.basic_wage_aed == Decimal(1600)
    assert "unpaid_wages" in facts.issue_types
    assert facts.termination == "still_employed"
