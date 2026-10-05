"""Keep the analysis from contradicting the calculator (CHANGES.md 24).

On 4 Oct (TC-02, Urdu) the Analyst miscounted 2.3 years of service as under one year and put
"not entitled to gratuity" in not_covered; the Writer repeated it to the worker next to a
calculated gratuity. Agents now get the calculator's service length, and this guard drops any
not_covered note that denies an item the calculator paid.

In the 5 Oct evaluation, K2 still cited Art. 43 (notice) as broken when the full notice had been
served (N-01, N-11, N-18), despite the prompt rule (CHANGES.md 27). `drop_ruled_out_notice` removes
those citations in code. Your decision (5 Oct, N-12): contracts from before the 2021 law also use
the contract notice, not Art. 65(6)'s notice by length of service, so Art. 65(6) is dropped too.
"""

import logging
import re

from haqqi.agents.schemas import AnalystReply
from haqqi.core.calculator import CalcResult, notice_shortfall_days
from haqqi.models import CaseFacts

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


# Notice clauses: Art. 43, and Art. 65(6) for pre-2022 contracts (also on the contract notice).
NOTICE_CLAUSES = ("fdl33-2021:art43:", "fdl33-2021:art65:cl6")


def notice_served_in_full(facts: CaseFacts) -> bool:
    return facts.termination in ("employer", "resigned") and notice_shortfall_days(facts) == 0


def drop_ruled_out_notice(reply: AnalystReply, facts: CaseFacts) -> AnalystReply:
    """With the full notice served, no notice clause can be the one broken: drop those citations."""
    if not notice_served_in_full(facts):
        return reply
    issues = []
    removed = 0
    for issue in reply.issues:
        kept = [c for c in issue.chunk_ids if not c.startswith(NOTICE_CLAUSES)]
        if len(kept) == len(issue.chunk_ids):
            issues.append(issue)
            continue
        removed += 1
        if kept:
            issues.append(issue.model_copy(update={"chunk_ids": kept}))
    if not removed:
        return reply
    log.warning("dropped notice citations from %d findings: the full notice was served", removed)
    return reply.model_copy(update={"issues": issues})
