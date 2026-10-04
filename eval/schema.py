"""The evaluation case format (task 7.1). One JSON object per line in eval/cases.jsonl.

A case is what a worker would type (story + form), what they would answer on the confirm form,
and what a correct result looks like. Expected money is worked out by hand in eval/CASES.md,
never copied from the calculator.
"""

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from haqqi.models import IssueType, Language

Route = Literal["ready", "out_of_scope", "need_info"]
ReferralKind = Literal["domestic", "difc_adgm", "free_zone"]


class Expected(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route: Route
    referral_kind: ReferralKind | None = None
    issues: list[IssueType] = []
    # Clauses that should be found (retrieval hit@5), and articles whose citation counts as
    # supported (flag 24).
    key_clauses: list[str] = []
    supporting_articles: list[str] = []
    # Hand-worked money: calculator item name → amount (None = "not calculated").
    claim: dict[str, Decimal | None] = {}
    worker_owes: dict[str, Decimal | None] = {}
    total: Decimal | None = None
    max_total: Decimal | None = None
    expect_not_covered: bool = False


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source: str  # "n8n TC-xx" or "new (7.2)"
    language: Language
    story: str
    contract_text: str | None = None
    form: dict[str, Any] = {}  # fields of CreateCaseRequest other than language/story/contract_text
    confirm: dict[str, Any] = {}  # what the worker confirms or corrects on the confirm form
    seed_bad_citation: bool = False
    injected_amounts: list[Decimal] = []  # figures planted in the story that must never appear
    expected: Expected
    notes: str = ""
    tags: list[str] = Field(default_factory=list)
