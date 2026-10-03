"""Case API end to end on a local Postgres, with a scripted LLM and the hash embedder.

Live tests: run `make dev` (or the db service), then `make test-live`.
"""

import json
from collections.abc import Iterator
from decimal import Decimal
from typing import Any

import psycopg
import pytest
from fastapi.testclient import TestClient

from haqqi.api import cases
from haqqi.api.main import create_app
from haqqi.models import Analysis, ExtractedFacts
from haqqi.rag.embed import HashEmbedder
from haqqi.rag.ingest import ingest
from tests.agents.fakes import FakeLLM
from tests.agents.test_analysis import PASS, WAGES, reply
from tests.agents.test_writer import writer

WAGE_LINE = ["Unpaid wages: [[AMOUNT_1]]"]

pytestmark = pytest.mark.live

TC01 = {
    "language": "hi",
    "story": "पिछले 3 महीने से मेरी तनख्वाह नहीं मिली है। मैं अभी भी वहीं काम कर रहा हूँ।",
    "emirate": "ajman",
    "zone": "mainland",
    "worker_type": "private_sector",
    "start_date": "2023-02-01",
    "basic_wage_aed": "1200",
    "total_wage_aed": "1800",
}
TC01_EXTRACTED = ExtractedFacts(
    issue_types=["unpaid_wages"],
    months_unpaid=3,
    termination="still_employed",
    facts_summary_en="Salary unpaid for three months; still employed.",
)


@pytest.fixture
def db(local_db_url: str) -> Iterator[str]:
    with psycopg.connect(local_db_url) as conn:
        ingest(conn, HashEmbedder())
    yield local_db_url


def client_with(llm: FakeLLM, db_url: str, hooks: bool = False) -> TestClient:
    app = create_app()
    app.dependency_overrides[cases.get_llm] = lambda: llm
    app.dependency_overrides[cases.get_embedder_dep] = lambda: HashEmbedder()
    app.dependency_overrides[cases.get_database_url] = lambda: db_url
    app.dependency_overrides[cases.get_test_hooks] = lambda: hooks
    return TestClient(app)


def events(body: str) -> list[tuple[str, Any]]:
    out = []
    for block in body.strip().split("\n\n"):
        name, data = block.split("\n", 1)
        out.append((name.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return out


def test_tc01_create_confirm_analyze_streams_stages_then_analysis(db: str) -> None:
    llm = FakeLLM(
        {
            "intake": [TC01_EXTRACTED],
            "analyst": [reply(WAGES)],
            "critic": [PASS],
            "writer": [
                writer(arabic_letter="إلى الوزارة: المطالبة [[AMOUNT_1]]", amount_lines=WAGE_LINE)
            ],
        }
    )
    client = client_with(llm, db)

    created = client.post("/v1/cases", json=TC01)
    assert created.status_code == 201, created.text
    case = created.json()
    assert case["status"] == "ready"
    assert case["extracted"]["total_wage_aed"] == "1800"  # the form wins

    confirmed = client.patch(f"/v1/cases/{case['id']}", json={"months_unpaid": 3})
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "confirmed"
    assert "story" not in confirmed.json()["confirmed"]

    streamed = client.post(f"/v1/cases/{case['id']}/analyze")
    assert streamed.headers["content-type"].startswith("text/event-stream")
    assert streamed.headers["cache-control"] == "no-cache"
    assert streamed.headers["x-accel-buffering"] == "no"
    got = events(streamed.text)
    assert [name for name, _ in got] == [
        "retrieving",
        "calculating",
        "analysing",
        "critiquing",
        "writing",
        "done",
    ]
    analysis = Analysis.model_validate(got[-1][1])
    assert analysis.total_aed == Decimal("5400.00")
    assert analysis.violations and analysis.writer
    assert "5,400.00 درهم" in analysis.writer.arabic_letter

    with psycopg.connect(db) as conn:
        row = conn.execute("SELECT status FROM cases WHERE id = %s", (case["id"],)).fetchone()
    assert row == ("analysed",)

    # A reload fetches the stored case and its analysis back; the story never leaves the server.
    fetched = client.get(f"/v1/cases/{case['id']}")
    assert fetched.status_code == 200, fetched.text
    body = fetched.json()
    assert body["status"] == "analysed"
    assert Analysis.model_validate(body["analysis"]) == analysis
    assert TC01["story"] not in fetched.text


def test_tc07_difc_is_referred_without_analysis(db: str) -> None:
    llm = FakeLLM({"intake": [ExtractedFacts(zone="difc", issue_types=["unpaid_wages"])]})
    client = client_with(llm, db)

    case = client.post(
        "/v1/cases", json={"language": "en", "story": "Fintech company in DIFC ended my contract."}
    ).json()
    assert case["status"] == "out_of_scope"
    assert "DIFC" in case["referral"] and "80084" in case["referral"]
    assert case["referral_kind"] == "difc_adgm"

    ((name, data),) = events(client.post(f"/v1/cases/{case['id']}/analyze").text)
    assert name == "done"
    assert data["in_scope"] is False and data["violations"] == []
    assert llm.stages() == ["intake"]  # no analysis calls


def test_need_info_names_the_form_fields_to_fill(db: str) -> None:
    llm = FakeLLM({"intake": [ExtractedFacts(issue_types=["unpaid_wages"])]})
    client = client_with(llm, db)

    case = client.post("/v1/cases", json={"language": "en", "story": "They stopped paying me."})
    body = case.json()
    assert body["status"] == "need_info"
    assert body["missing_fields"] == ["basic_wage_aed", "total_wage_aed", "start_date"]
    assert body["referral_kind"] is None and body["analysis"] is None

    fetched = client.get(f"/v1/cases/{body['id']}").json()
    assert fetched["status"] == "need_info" and fetched["missing_fields"] == body["missing_fields"]


def test_guards_unknown_case_unconfirmed_case_and_story_edits(db: str) -> None:
    llm = FakeLLM({"intake": [TC01_EXTRACTED]})
    client = client_with(llm, db)
    case = client.post("/v1/cases", json=TC01).json()

    assert client.post(f"/v1/cases/{case['id']}/analyze").status_code == 409
    assert client.patch(f"/v1/cases/{case['id']}", json={"story": "new"}).status_code == 422
    assert client.patch(f"/v1/cases/{case['id']}", json={"total_wage_aed": "-1"}).status_code == 422
    unknown = "00000000-0000-4000-8000-000000000000"
    assert client.patch(f"/v1/cases/{unknown}", json={}).status_code == 404
    assert client.get(f"/v1/cases/{unknown}").status_code == 404
    assert client.get("/v1/cases/not-a-uuid").status_code == 422


def test_seeded_bad_citation_needs_the_test_hooks_setting(db: str) -> None:
    def run(hooks: bool) -> str:
        llm = FakeLLM(
            {
                "intake": [TC01_EXTRACTED],
                "analyst": [reply(WAGES)],
                "critic": [PASS],
                "writer": [
                    writer(arabic_letter="إلى الوزارة: [[AMOUNT_1]]", amount_lines=WAGE_LINE)
                ],
            }
        )
        client = client_with(llm, db, hooks=hooks)
        case_id = client.post("/v1/cases", json=TC01).json()["id"]
        client.patch(f"/v1/cases/{case_id}", json={})
        client.post(f"/v1/cases/{case_id}/analyze?seed_bad_citation=true")
        return llm.calls[2][1][1].content.split("ANALYSIS:")[1]  # what the critic saw

    assert "art54:cl9" not in run(hooks=False)
    assert "art54:cl9" in run(hooks=True)
