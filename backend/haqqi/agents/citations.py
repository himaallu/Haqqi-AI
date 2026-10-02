"""Citation enforcement (task 3.8; ports `enforceCitations` in n8n Parse Analyst/Revision).

A finding may cite only clauses that retrieval actually gave the model. Any other id is
dropped; a finding left with no valid citation is moved to not_covered. Quotes shown to the
worker come from our law text, never from the model.
"""

from collections.abc import Collection, Sequence

from haqqi.agents.schemas import AnalystReply
from haqqi.models import Citation, Violation
from haqqi.rag.retrieve import RetrievedChunk


def enforce_citations(reply: AnalystReply, allowed_ids: Collection[str]) -> AnalystReply:
    allowed = set(allowed_ids)
    issues = []
    not_covered = list(reply.not_covered)
    for issue in reply.issues:
        valid = [cid for cid in dict.fromkeys(issue.chunk_ids) if cid in allowed]
        if valid:
            issues.append(issue.model_copy(update={"chunk_ids": valid}))
        else:
            not_covered.append(issue.finding)
    return reply.model_copy(update={"issues": issues, "not_covered": not_covered})


def to_violations(reply: AnalystReply, law: Sequence[RetrievedChunk]) -> list[Violation]:
    """One `Violation` per cited clause; call after `enforce_citations`."""
    by_id = {chunk.id: chunk for chunk in law}
    violations = []
    for issue in reply.issues:
        for cid in issue.chunk_ids:
            chunk = by_id[cid]
            violations.append(
                Violation(
                    issue=issue.finding,
                    article=Citation(
                        chunk_id=chunk.id,
                        law_id=chunk.id.split(":", 1)[0],
                        article_no=chunk.article_no,
                        clause_no=chunk.clause_no,
                        quote=chunk.text_en,
                    ),
                    confidence=issue.confidence,
                )
            )
    return violations
