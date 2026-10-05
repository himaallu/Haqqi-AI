"""Analyst → Critic → at most one revision (task 3.9).

Ports Build/K2/Parse Analyst, Build/K2/Parse Critic, Critic Passed? and Build/K2/Parse Revision.
Citations are enforced after every model reply, so the Critic and the Writer only ever see
clauses that retrieval returned.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from haqqi.agents.citations import enforce_citations
from haqqi.agents.consistency import drop_contradictions, drop_ruled_out_notice
from haqqi.agents.messages import analyst_messages, critic_messages, revision_messages
from haqqi.agents.schemas import AnalystReply
from haqqi.core.calculator import CalcResult
from haqqi.llm.client import Completer
from haqqi.models import CaseFacts, CriticReport
from haqqi.rag.retrieve import RetrievedChunk

# TC-11: a real clause about something else (the 2-year time limit), which the Critic must catch.
SEEDED_BAD_CITATION = "fdl33-2021:art54:cl9"


@dataclass(frozen=True)
class AnalysisRun:
    reply: AnalystReply
    critic: CriticReport
    revised: bool


def run_analysis(
    client: Completer,
    facts: CaseFacts,
    law: Sequence[RetrievedChunk],
    calc: CalcResult,
    *,
    seed_bad_citation: bool = False,
    on_stage: Callable[[str], None] = lambda _stage: None,
) -> AnalysisRun:
    """`seed_bad_citation` must only be passed when settings.haqqi_test_hooks is on."""
    allowed = {chunk.id for chunk in law}

    on_stage("analysing")
    reply = client.complete("analyst", analyst_messages(facts, law, calc), AnalystReply)
    reply = drop_ruled_out_notice(
        drop_contradictions(enforce_citations(reply, allowed), calc), facts
    )
    if seed_bad_citation and reply.issues and SEEDED_BAD_CITATION in allowed:
        first = reply.issues[0].model_copy(update={"chunk_ids": [SEEDED_BAD_CITATION]})
        reply = reply.model_copy(update={"issues": [first, *reply.issues[1:]]})

    on_stage("critiquing")
    critic = client.complete("critic", critic_messages(facts, law, calc, reply), CriticReport)
    if critic.verdict == "pass":
        return AnalysisRun(reply, critic, revised=False)

    on_stage("revising")
    revised = client.complete(
        "revision", revision_messages(facts, law, calc, reply, critic), AnalystReply
    )
    revised = drop_contradictions(enforce_citations(revised, allowed), calc)
    return AnalysisRun(drop_ruled_out_notice(revised, facts), critic, revised=True)
