"""Load eval/cases.jsonl and build the facts a case confirms (no LLM)."""

import json
from pathlib import Path
from typing import Any

from eval.schema import Case
from haqqi.api.schemas import CreateCaseRequest
from haqqi.models import CaseFacts

CASES_FILE = Path(__file__).with_name("cases.jsonl")


def load_cases(path: Path = CASES_FILE) -> list[Case]:
    cases = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            try:
                cases.append(Case.model_validate_json(line))
            except ValueError as exc:
                raise ValueError(f"{path.name} line {n}: {exc}") from None
    return cases


def create_request(case: Case) -> CreateCaseRequest:
    return CreateCaseRequest.model_validate(
        {
            "language": case.language,
            "story": case.story,
            "contract_text": case.contract_text,
            **case.form,
        }
    )


def confirmed_facts(case: Case, extracted: dict[str, Any] | None = None) -> CaseFacts:
    """What the worker confirms: the Intake's extraction, then the form, then their answers on the
    confirm form. Offline (no Intake) the form and the confirm answers alone describe the case."""
    base = {
        k: v for k, v in (extracted or {}).items() if v is not None and k in CaseFacts.model_fields
    }
    form = {k: v for k, v in case.form.items() if v is not None}
    return CaseFacts.model_validate(
        {
            **base,
            **form,
            **case.confirm,
            "language": case.language,
            "story": case.story,
            "contract_text": case.contract_text,
        }
    )


def dumps(case: dict[str, Any]) -> str:
    return json.dumps(case, ensure_ascii=False)
