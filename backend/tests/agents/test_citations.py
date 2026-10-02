from haqqi.agents.citations import enforce_citations, to_violations
from haqqi.agents.schemas import AnalystIssue, AnalystReply
from haqqi.rag.retrieve import RetrievedChunk

ART22 = RetrievedChunk(
    id="fdl33-2021:art22:cl2",
    article_no=22,
    clause_no=2,
    title="Wages",
    text_en="The Employer is obligated to pay the wages on their due dates.",
    text_ar="",
    source="pack",
)


def issue(finding: str, *ids: str) -> AnalystIssue:
    return AnalystIssue(
        issue_type="unpaid_wages",
        finding=finding,
        chunk_ids=list(ids),
        confidence="high",
        evidence="e",
    )


def test_fabricated_ids_are_removed_and_uncited_findings_move_to_not_covered() -> None:
    reply = AnalystReply(
        issues=[
            issue("Wages unpaid", "fdl33-2021:art22:cl2", "fdl33-2021:art999:cl1"),
            issue("Invented right", "fdl33-2021:art777"),
        ],
        not_covered=["Visa fines"],
    )

    enforced = enforce_citations(reply, {ART22.id})

    assert [i.chunk_ids for i in enforced.issues] == [["fdl33-2021:art22:cl2"]]
    assert enforced.not_covered == ["Visa fines", "Invented right"]


def test_violation_quotes_come_from_our_law_text() -> None:
    reply = enforce_citations(
        AnalystReply(issues=[issue("Wages unpaid", ART22.id, ART22.id)]), {ART22.id}
    )
    (violation,) = to_violations(reply, [ART22])

    assert violation.article.quote == ART22.text_en
    assert violation.article.law_id == "fdl33-2021"
    assert (violation.article.article_no, violation.article.clause_no) == (22, 2)
