"""Request bodies for the case API (task 3.4). Limits are enforced before anything reaches K2."""

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from haqqi.core.untrusted import clean_text
from haqqi.models import Emirate, Language, WorkerType, Zone

MAX_STORY_CHARS = 8000
MAX_CONTRACT_CHARS = 4000

Story = Annotated[str, AfterValidator(clean_text), Field(min_length=1, max_length=MAX_STORY_CHARS)]
ContractText = Annotated[str, AfterValidator(clean_text), Field(max_length=MAX_CONTRACT_CHARS)]


class CreateCaseRequest(BaseModel):
    """`POST /v1/cases`: the story plus whatever the worker filled in on the form."""

    model_config = ConfigDict(extra="forbid")

    language: Language
    story: Story
    contract_text: ContractText | None = None
    emirate: Emirate | None = None
    zone: Zone | None = None  # None = "not sure"
    worker_type: WorkerType | None = None
    start_date: date | None = None
    end_date: date | None = None
    basic_wage_aed: Decimal | None = Field(default=None, ge=0, le=1_000_000)
    total_wage_aed: Decimal | None = Field(default=None, ge=0, le=1_000_000)
