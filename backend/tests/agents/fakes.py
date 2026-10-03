"""A scripted stand-in for `LLMClient` so agent logic is tested without K2."""

from collections.abc import Sequence

from pydantic import BaseModel

from haqqi.llm.client import Message


class FakeLLM:
    def __init__(self, replies: dict[str, list[BaseModel]]) -> None:
        self.replies = {stage: list(items) for stage, items in replies.items()}
        self.calls: list[tuple[str, list[Message]]] = []

    def complete[T: BaseModel](self, stage: str, messages: Sequence[Message], schema: type[T]) -> T:
        self.calls.append((stage, list(messages)))
        reply = self.replies[stage].pop(0)
        return schema.model_validate(reply.model_dump())

    def stages(self) -> list[str]:
        return [stage for stage, _ in self.calls]
