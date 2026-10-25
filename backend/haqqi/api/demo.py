"""Pitch-demo API (docs/demo/LOVABLE_PROMPT.md): the Ask door over the real law index.

POST /v1/demo/ask  question + language → a short cited answer, "unsure" or "off_topic"

Nothing is stored and the question is never logged. Cases use the normal /v1/cases endpoints.
"""

import logging
from collections.abc import Callable
from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from haqqi import tracing
from haqqi.agents.ask import Kind, run_ask
from haqqi.agents.messages import clause_ref
from haqqi.api.cases import DbUrl, EmbedderDep, Llm, _llm_http_error
from haqqi.core.untrusted import clean_text
from haqqi.llm.client import LLMError
from haqqi.models import Language
from haqqi.rag.embed import Embedder
from haqqi.rag.lawdata import load_law_pack
from haqqi.rag.retrieve import RetrievedChunk, retrieve

log = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/demo")

MAX_QUESTION_CHARS = 1000
Search = Callable[[str], list[RetrievedChunk]]


class Contact(BaseModel):
    label: str
    number: str


# Fixed by code, never by the model (docs/research/desk_research.md §2).
MOHRE = [
    Contact(label="MOHRE labour claims and advice", number="80084"),
    Contact(label="MOHRE WhatsApp", number="600590000"),
]
EMERGENCY = [
    Contact(label="Police (emergency)", number="999"),
    Contact(label="Human trafficking hotline (800 SAVE)", number="8007283"),
]


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: Language
    question: Annotated[
        str, AfterValidator(clean_text), Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    ]


class CitedClause(BaseModel):
    chunk_id: str
    ref_en: str  # e.g. "Art. 13(2), Federal Decree-Law No. 33 of 2021"
    ref_ar: str
    title: str
    text_en: str  # official text, from our law data
    text_ar: str


class AskResponse(BaseModel):
    kind: Kind
    headline: str  # in the worker's language; empty unless kind == "answer"
    answer: str
    citations: list[CitedClause]
    suggest_case: bool
    safety: bool
    contacts: list[Contact]  # emergency numbers first when safety is true


def get_search(embedder: EmbedderDep, db_url: DbUrl) -> Search:
    return lambda text: _search(db_url, embedder, text)


def _search(db_url: str, embedder: Embedder, text: str) -> list[RetrievedChunk]:
    with psycopg.connect(db_url) as conn:
        return retrieve(conn, text, embedder, load_law_pack())


@router.post("/ask")
def ask(req: AskRequest, llm: Llm, search: Annotated[Search, Depends(get_search)]) -> AskResponse:
    try:
        with tracing.trace("demo_ask", language=req.language):
            result = run_ask(llm, req.question, req.language, search(req.question))
    except LLMError as exc:
        raise _llm_http_error(exc) from None
    except psycopg.Error:
        log.warning("demo ask: law search failed")
        raise HTTPException(503, "The law search is not available. Please try again.") from None
    return AskResponse(
        kind=result.kind,
        headline=result.headline,
        answer=result.answer,
        citations=[
            CitedClause(
                chunk_id=c.id,
                ref_en=clause_ref(c),
                ref_ar=clause_ref(c, "ar"),
                title=c.title,
                text_en=c.text_en,
                text_ar=c.text_ar,
            )
            for c in result.cited
        ],
        suggest_case=result.suggest_case,
        safety=result.safety,
        contacts=(EMERGENCY if result.safety else []) + MOHRE,
    )
