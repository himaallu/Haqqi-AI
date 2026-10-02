"""JSON shapes the agents must return. Every reply is validated against one of these.

Intake returns `haqqi.models.ExtractedFacts`, the Critic `CriticReport`, the Writer
`WriterOutput`. None of them has a money field: amounts come only from the calculator.
"""

from pydantic import BaseModel, ConfigDict

from haqqi.models import Confidence, IssueType


class _Reply(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnalystIssue(_Reply):
    issue_type: IssueType
    finding: str  # one or two sentences: why the facts likely breach the cited clause
    chunk_ids: list[str]  # ids from LAW only, e.g. fdl33-2021:art22:cl2
    confidence: Confidence
    evidence: str  # the facts that support the finding


class AnalystReply(_Reply):
    issues: list[AnalystIssue]
    not_covered: list[str] = []
    time_limit_note: str = ""
    next_steps: list[str] = []
    documents_to_gather: list[str] = []
