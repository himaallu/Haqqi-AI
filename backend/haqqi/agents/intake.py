"""Intake agent: story + form → `ExtractedFacts` (task 3.7; ports Build/K2/Parse Intake)."""

from haqqi.agents.messages import intake_messages
from haqqi.api.schemas import CreateCaseRequest
from haqqi.llm.client import Completer
from haqqi.models import ExtractedFacts

FORM_FIELDS = (
    "emirate",
    "zone",
    "worker_type",
    "start_date",
    "end_date",
    "basic_wage_aed",
    "total_wage_aed",
)


def run_intake(client: Completer, req: CreateCaseRequest) -> ExtractedFacts:
    extracted = client.complete("intake", intake_messages(req), ExtractedFacts)
    # What the worker typed on the form always beats what the model read from the story.
    form = {f: getattr(req, f) for f in FORM_FIELDS if getattr(req, f) is not None}
    if not extracted.issue_types:
        form["issue_types"] = ["other"]
    return extracted.model_copy(update={**form, "language": req.language})
