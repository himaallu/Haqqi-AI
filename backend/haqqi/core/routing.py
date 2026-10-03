"""After intake: refer the case, ask for more facts, or analyse it (task 3.3).

Deterministic. What the worker chose on the form beats what the model read from the story,
so text in the story cannot talk its way into or out of scope (TC-14). v1 analyses
mainland private-sector cases only (flag 1).
"""

from dataclasses import dataclass, field
from typing import Literal

from haqqi.models import ExtractedFacts, WorkerType, Zone

Route = Literal["out_of_scope", "need_info", "ready"]
Referral = Literal["domestic", "difc_adgm", "free_zone"]

MOHRE_CONTACT = "MOHRE: call 80084 or use the MOHRE app."
REFERRALS: dict[Referral, str] = {
    "domestic": "Domestic workers are covered by a separate law that Haqqi does not analyse. "
    "Contact MOHRE about your case. " + MOHRE_CONTACT,
    "difc_adgm": "DIFC and ADGM have their own employment laws and courts, so the federal "
    "labour law does not apply. Use the DIFC or ADGM courts' employment services. " + MOHRE_CONTACT,
    "free_zone": "Federal gratuity rules broadly apply in most free zones, but complaints go to "
    "your free zone authority first, not MOHRE. Contact your free zone authority. " + MOHRE_CONTACT,
}

MISSING_WAGE = "Your monthly salary in AED"
MISSING_START = "The date you started this job"
# The form fields the UI highlights for each missing fact.
MISSING_FIELDS: dict[str, list[str]] = {
    MISSING_WAGE: ["basic_wage_aed", "total_wage_aed"],
    MISSING_START: ["start_date"],
}


@dataclass(frozen=True)
class RouteDecision:
    route: Route
    zone: Zone | None
    worker_type: WorkerType | None
    referral: Referral | None = None
    missing: list[str] = field(default_factory=list)

    @property
    def referral_text(self) -> str | None:
        return REFERRALS[self.referral] if self.referral else None


def route_case(
    extracted: ExtractedFacts,
    form_zone: Zone | None = None,
    form_worker_type: WorkerType | None = None,
) -> RouteDecision:
    """`form_*` are the worker's answers; None ("not sure") falls back to the model."""
    zone = form_zone or extracted.zone
    worker_type = form_worker_type or extracted.worker_type

    referral: Referral | None = None
    if worker_type == "domestic":
        referral = "domestic"
    elif zone in ("difc", "adgm"):
        referral = "difc_adgm"
    elif zone == "free_zone":
        referral = "free_zone"
    if referral:
        return RouteDecision("out_of_scope", zone, worker_type, referral=referral)

    missing = []
    if extracted.basic_wage_aed is None and extracted.total_wage_aed is None:
        missing.append(MISSING_WAGE)
    if extracted.start_date is None:
        missing.append(MISSING_START)
    if missing:
        return RouteDecision("need_info", zone, worker_type, missing=missing)
    return RouteDecision("ready", zone, worker_type)
