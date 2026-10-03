import pytest

from haqqi.agents.analysis import SEEDED_BAD_CITATION, run_analysis
from haqqi.agents.schemas import AnalystIssue, AnalystReply
from haqqi.config import Settings
from haqqi.core.calculator import calculate
from haqqi.llm.client import LLMClient
from haqqi.models import CaseFacts, CriticProblem, CriticReport
from haqqi.rag.lawdata import load_chunks, load_law_pack
from haqqi.rag.retrieve import RetrievedChunk
from tests.agents.fakes import FakeLLM

WAGES = "fdl33-2021:art22:cl2"

FACTS = CaseFacts.model_validate(
    {
        "language": "en",
        "emirate": "dubai",
        "zone": "mainland",
        "worker_type": "private_sector",
        "start_date": "2024-09-01",
        "basic_wage_aed": "1800",
        "total_wage_aed": "2400",
        "months_unpaid": 2,
        "termination": "still_employed",
        "issue_types": ["unpaid_wages"],
        "story": "I have not received my salary for the last two months. "
        "My manager keeps saying next week.",
    }
)


def pack_law(*issue_types: str) -> list[RetrievedChunk]:
    by_id = {c.id: c for c in load_chunks()}
    return [
        RetrievedChunk(
            id=cid,
            article_no=by_id[cid].article_no,
            clause_no=by_id[cid].clause_no,
            title=by_id[cid].title,
            text_en=by_id[cid].text_en,
            text_ar=by_id[cid].text_ar,
            source="pack",
        )
        for cid in load_law_pack().chunk_ids_for(list(issue_types))
    ]


def reply(*ids: str) -> AnalystReply:
    return AnalystReply(
        issues=[
            AnalystIssue(
                issue_type="unpaid_wages",
                finding="Wages unpaid for two months.",
                chunk_ids=list(ids),
                confidence="high",
                evidence="two months",
            )
        ]
    )


PASS = CriticReport(verdict="pass")
REVISE = CriticReport(
    verdict="revise",
    problems=[CriticProblem(where="issues[0]", problem="wrong clause", fix="cite 22")],
)


def test_pass_needs_no_revision() -> None:
    llm = FakeLLM({"analyst": [reply(WAGES)], "critic": [PASS]})
    stages: list[str] = []

    run = run_analysis(
        llm, FACTS, pack_law("unpaid_wages"), calculate(FACTS), on_stage=stages.append
    )

    assert not run.revised
    assert llm.stages() == ["analyst", "critic"]
    assert stages == ["analysing", "critiquing"]


def test_at_most_one_revision_and_it_is_citation_checked() -> None:
    llm = FakeLLM(
        {
            "analyst": [reply(WAGES)],
            "critic": [REVISE, REVISE],
            "revision": [reply(WAGES, "fdl33-2021:art999:cl1")],
        }
    )

    run = run_analysis(llm, FACTS, pack_law("unpaid_wages"), calculate(FACTS))

    assert run.revised
    assert llm.stages() == ["analyst", "critic", "revision"]  # no second critic round
    assert run.reply.issues[0].chunk_ids == [WAGES]  # invented id dropped


def test_seeded_bad_citation_reaches_the_critic() -> None:
    llm = FakeLLM({"analyst": [reply(WAGES)], "critic": [PASS]})

    run_analysis(llm, FACTS, pack_law("unpaid_wages"), calculate(FACTS), seed_bad_citation=True)

    critic_input = llm.calls[1][1][1].content
    assert SEEDED_BAD_CITATION in critic_input.split("ANALYSIS:")[1]
    assert WAGES not in critic_input.split("ANALYSIS:")[1]


@pytest.mark.live
def test_live_tc11_critic_catches_the_seeded_bad_citation() -> None:
    settings = Settings()
    if not settings.k2_api_key:
        pytest.skip("K2_API_KEY not set")
    client = LLMClient.from_settings(settings)

    run = run_analysis(
        client, FACTS, pack_law("unpaid_wages"), calculate(FACTS), seed_bad_citation=True
    )

    assert run.critic.verdict == "revise"
    assert run.revised
    cited = {cid for issue in run.reply.issues for cid in issue.chunk_ids}
    wage_issues = [i for i in run.reply.issues if i.issue_type == "unpaid_wages"]
    assert wage_issues and all(SEEDED_BAD_CITATION not in i.chunk_ids for i in wage_issues)
    assert cited
