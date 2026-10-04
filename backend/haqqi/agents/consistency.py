"""Keep the analysis from contradicting the calculator (CHANGES.md 24).

On 4 Oct (TC-02, Urdu) the Analyst miscounted 2.3 years of service as under one year and put
"not entitled to gratuity" in not_covered; the Writer repeated it to the worker next to a
calculated gratuity. Agents now get the calculator's service length, and this guard drops any
not_covered note that denies an item the calculator paid.
"""

import logging
import re

from haqqi.agents.schemas import AnalystReply
from haqqi.core.calculator import CalcResult

log = logging.getLogger(__name__)

# Words that name each calculated item in the Analyst's English text.
ITEM_WORDS = {
    "End-of-service gratuity": ("gratuity", "end-of-service", "end of service"),
    "Notice pay": ("notice",),
    "Unpaid wages": ("unpaid wage", "unpaid salary", "wages", "salary"),
    "Deductions from wages": ("deduction",),
    "Unused annual leave": ("leave",),
}
DENIAL = re.compile(
    r"\b(not (entitled|eligible|owed|due)|ineligible|no right|does not qualify|doesn't qualify"
    r"|has not completed)\b",
    re.IGNORECASE,
)


def drop_contradictions(reply: AnalystReply, calc: CalcResult) -> AnalystReply:
    paid = [line.item for line in calc.claim if line.amount_aed is not None and line.amount_aed > 0]
    words = [w for item in paid for w in ITEM_WORDS.get(item, ())]
    kept = []
    for note in reply.not_covered:
        lowered = note.lower()
        if DENIAL.search(note) and any(w in lowered for w in words):
            log.warning("dropped a not_covered note that contradicts a calculated claim")
            continue
        kept.append(note)
    if len(kept) == len(reply.not_covered):
        return reply
    return reply.model_copy(update={"not_covered": kept})
