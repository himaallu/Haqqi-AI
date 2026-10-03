"""One confirmed case → `Analysis` (task 3.11; ports the n8n graph and Assemble Case Pack).

retrieve → calculate → Analyst/Critic/one revision → Writer. Each stage is reported through
`emit` so the API can stream progress (F8). Money comes only from the calculator.
"""

from collections.abc import Callable, Sequence

from haqqi.agents.analysis import run_analysis
from haqqi.agents.citations import to_violations
from haqqi.agents.writer import run_writer
from haqqi.core.calculator import calculate
from haqqi.llm.client import Completer
from haqqi.models import Analysis, CaseFacts, IssueType
from haqqi.rag.retrieve import RetrievedChunk

Search = Callable[[str, Sequence[IssueType]], list[RetrievedChunk]]
Emit = Callable[[str], None]


def analyze_case(
    facts: CaseFacts,
    query: str,
    llm: Completer,
    search: Search,
    emit: Emit,
    *,
    seed_bad_citation: bool = False,
) -> Analysis:
    emit("retrieving")
    law = search(query, facts.issue_types)

    emit("calculating")
    calc = calculate(facts)

    run = run_analysis(llm, facts, law, calc, seed_bad_citation=seed_bad_citation, on_stage=emit)

    emit("writing")
    writer = run_writer(llm, facts, run.reply, calc)

    return Analysis(
        in_scope=True,
        violations=to_violations(run.reply, law),
        not_covered=run.reply.not_covered,
        claim=calc.claim,
        worker_owes=calc.worker_owes,
        total_aed=calc.total_aed,
        above_mohre_limit=calc.above_mohre_limit,
        explanation=writer.explanation,
        next_steps=run.reply.next_steps,
        documents_to_gather=run.reply.documents_to_gather,
        time_limit_note=run.reply.time_limit_note,
        critic_verdict=run.critic.verdict,
        revised=run.revised,
        writer=writer,
    )
