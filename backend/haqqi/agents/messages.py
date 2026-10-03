"""Build each agent's messages. Worker text enters only through `wrap_worker_data` (task 3.4);
law enters as clause ids and official text; money enters the Writer only as tokens."""

from collections.abc import Sequence
from datetime import date

from haqqi.agents.schemas import AnalystReply
from haqqi.api.schemas import CreateCaseRequest
from haqqi.core.calculator import CalcResult
from haqqi.core.untrusted import wrap_worker_data
from haqqi.llm.client import Message, dump_json
from haqqi.models import CaseFacts, CriticReport
from haqqi.rag.prompts import system_prompt
from haqqi.rag.retrieve import RetrievedChunk

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "ur": "Urdu",
    "ml": "Malayalam",
    "bn": "Bengali",
    "tl": "Tagalog",
    "ne": "Nepali",
    "ar": "Arabic",
}
LAW_NAMES = {
    "fdl33-2021": ("Federal Decree-Law No. 33 of 2021", "المرسوم بقانون اتحادي رقم (33) لسنة 2021"),
    "cr1-2022": ("Cabinet Resolution No. 1 of 2022", "قرار مجلس الوزراء رقم (1) لسنة 2022"),
}


def clause_ref(chunk: RetrievedChunk | str, lang: str = "en") -> str:
    """Human reference for a clause id, e.g. "Art. 51(2), Federal Decree-Law No. 33 of 2021"."""
    chunk_id = chunk if isinstance(chunk, str) else chunk.id
    law_id, art, *clause = chunk_id.split(":")
    article = art.removeprefix("art")
    en, ar = LAW_NAMES.get(law_id, (law_id, law_id))
    if lang == "ar":
        clause_ar = f" البند ({clause[0].removeprefix('cl')})" if clause else ""
        return f"المادة ({article}){clause_ar} من {ar}"
    clause_en = f"({clause[0].removeprefix('cl')})" if clause else ""
    return f"Art. {article}{clause_en}, {en}"


def _law(chunks: Sequence[RetrievedChunk]) -> str:
    return dump_json([{"id": c.id, "title": c.title, "text": c.text_en} for c in chunks])


def _facts(facts: CaseFacts) -> str:
    data = facts.model_dump(mode="json", exclude={"story", "contract_text"})
    worker_text = facts.story + (
        f"\n\nContract text:\n{facts.contract_text}" if facts.contract_text else ""
    )
    return dump_json(data) + "\n\nWorker's own words:\n" + wrap_worker_data(worker_text)


def intake_messages(req: CreateCaseRequest, today: date | None = None) -> list[Message]:
    """`today` lets the model place dates told without a year (tests pass a fixed date)."""
    form = req.model_dump(mode="json", exclude={"story", "contract_text"}, exclude_none=True)
    worker_text = req.story + (
        f"\n\nContract text:\n{req.contract_text}" if req.contract_text else ""
    )
    user = (
        f"TODAY: {(today or date.today()).isoformat()}\n\n"
        f"FORM (chosen by the worker):\n{dump_json(form)}\n\n"
        f"STORY:\n{wrap_worker_data(worker_text)}"
    )
    return [Message("system", system_prompt("intake")), Message("user", user)]


def _claim_items(calc: CalcResult) -> str:
    return dump_json(
        [
            {"item": line.item, "calculated": line.amount_aed is not None}
            for line in [*calc.claim, *calc.worker_owes]
        ]
    )


def analyst_messages(
    facts: CaseFacts, law: Sequence[RetrievedChunk], calc: CalcResult
) -> list[Message]:
    user = f"FACTS:\n{_facts(facts)}\n\nLAW:\n{_law(law)}\n\nCLAIM_ITEMS:\n{_claim_items(calc)}"
    return [Message("system", system_prompt("analyst")), Message("user", user)]


def critic_messages(
    facts: CaseFacts, law: Sequence[RetrievedChunk], analysis: AnalystReply
) -> list[Message]:
    user = (
        f"FACTS:\n{_facts(facts)}\n\nLAW:\n{_law(law)}\n\n"
        f"ANALYSIS:\n{analysis.model_dump_json(indent=1)}"
    )
    return [Message("system", system_prompt("critic")), Message("user", user)]


def revision_messages(
    facts: CaseFacts,
    law: Sequence[RetrievedChunk],
    calc: CalcResult,
    analysis: AnalystReply,
    critic: CriticReport,
) -> list[Message]:
    user = (
        f"FACTS:\n{_facts(facts)}\n\nLAW:\n{_law(law)}\n\nCLAIM_ITEMS:\n{_claim_items(calc)}\n\n"
        f"YOUR EARLIER ANALYSIS:\n{analysis.model_dump_json(indent=1)}\n\n"
        f"CRITIC FEEDBACK:\n{critic.model_dump_json(indent=1)}"
    )
    return [Message("system", system_prompt("revision")), Message("user", user)]


def amount_placeholder(index: int) -> str:
    return f"[[AMOUNT_{index}]]"


TOTAL_PLACEHOLDER = "[[TOTAL]]"


def writer_messages(facts: CaseFacts, analysis: AnalystReply, calc: CalcResult) -> list[Message]:
    claims = [
        {
            "token": amount_placeholder(i),
            "item": line.item,
            "formula": line.formula,
            "note": line.note,
        }
        for i, line in enumerate(calc.claim, start=1)
        if line.amount_aed is not None
    ]
    approved = {
        "issues": [
            {
                "issue_type": issue.issue_type,
                "finding": issue.finding,
                "references_en": [clause_ref(c) for c in issue.chunk_ids],
            }
            for issue in analysis.issues
        ],
        "not_covered": analysis.not_covered,
        "time_limit_note": analysis.time_limit_note,
        "next_steps": analysis.next_steps,
    }
    user = (
        f"FACTS:\n{_facts(facts)}\n\n"
        f"APPROVED ANALYSIS:\n{dump_json(approved)}\n\n"
        f"CLAIMS (total {TOTAL_PLACEHOLDER}):\n{dump_json(claims)}"
    )
    language = LANGUAGE_NAMES[facts.language]
    return [Message("system", system_prompt("writer", language=language)), Message("user", user)]
