"""Ask door for the pitch demo: one question → a short, cited answer in the worker's language.

One LLM call over the retrieved law (docs/CHAT_PLAN.md, Ask door). The same trust rules as the case
pipeline apply in code: only retrieved clause ids survive, an answer with none left becomes
"unsure", and a reply with any money figure gets one retry, then becomes "unsure". Only an
"answer" carries model text; the app shows its own fixed text for "unsure" and "off_topic".
"""

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict

from haqqi.agents.messages import ask_messages
from haqqi.agents.writer import ARABIC_DIGITS, GROUPED, MONEY
from haqqi.llm.client import Completer, correction
from haqqi.models import IssueType, Language
from haqqi.rag.retrieve import RetrievedChunk

log = logging.getLogger(__name__)

Kind = Literal["answer", "unsure", "off_topic"]

# Code also checks for danger words, so the emergency card doesn't depend on the model alone.
# English and Arabic (the demo's languages); the model's `safety` flag covers the others.
DANGER = re.compile(
    r"\b(beat(?:s|ing|en)?|hit(?:s|ting)? me|locked (?:in|up)|lock(?:s|ed)? me|no food|no water|"
    r"traffick\w*|forced to work|sexual(?:ly)?|rape\w*|threaten\w*|kill)\b"
    r"|يضرب|ضرب|حبس|محبوس|أغلق\s*علي|اتجار|تحرش|اعتداء|يهدد|تهديد|بدون\s*طعام|بلا\s*طعام"
    r"|بدون\s*ماء|بلا\s*ماء|العمل\s*القسري",
    re.IGNORECASE,
)


# Law Pack topics a question is about, from its words (English, Arabic, Hindi, Urdu). Search alone
# often misses the key article for a question in Arabic (Art. 13(2) for "جواز"), the same gap the
# retrieval probe found on 2 Oct; the topic adds its Law Pack articles and English search terms,
# as the Intake's issue types do for a case. Matching is plain substring search, no LLM call.
TOPIC_WORDS: dict[IssueType, tuple[str, ...]] = {
    "unpaid_wages": (
        "salary",
        "wage",
        "not paid",
        "unpaid",
        "راتب",
        "رواتب",
        "أجر",
        "الأجور",
        "तनख्वाह",
        "तनख़्वाह",
        "वेतन",
        "تنخواہ",
    ),
    "illegal_deduction": ("deduct", "cut my salary", "خصم", "يخصم", "कटौती", "کٹوتی"),
    "termination": (
        "fired",
        "terminat",
        "dismiss",
        "ended my job",
        "فصل",
        "إنهاء",
        "أنهى",
        "निकाल",
        "برطرف",
    ),
    "notice_pay": ("notice", "resign", "إنذار", "استقال", "نوٹس", "नोटिस", "इस्तीफ", "استعفی"),
    "gratuity": (
        "gratuity",
        "end of service",
        "end-of-service",
        "مكافأة",
        "نهاية الخدمة",
        "ग्रेच्युटी",
        "گریجویٹی",
    ),
    "leave": ("annual leave", "vacation", "holiday", "إجازة", "छुट्टी", "چھٹی"),
    "overtime": (
        "overtime",
        "extra hours",
        "working hours",
        "إضافي",
        "ساعات العمل",
        "ओवरटाइम",
        "اوور ٹائم",
    ),
    "document_retention": (
        "passport",
        "documents",
        "emirates id",
        "جواز",
        "وثائق",
        "الهوية",
        "पासपोर्ट",
        "پاسپورٹ",
    ),
}


def topics_in(question: str) -> list[IssueType]:
    text = question.lower()
    return [topic for topic, words in TOPIC_WORDS.items() if any(w in text for w in words)]


class AskReply(BaseModel):
    """What the model must return (haqqi/rag/prompts/demo_ask.md)."""

    model_config = ConfigDict(extra="forbid")

    kind: Kind
    headline: str = ""
    answer: str = ""
    chunk_ids: list[str] = []
    suggest_case: bool = False
    safety: bool = False


@dataclass(frozen=True)
class AskResult:
    kind: Kind
    headline: str
    answer: str
    cited: list[RetrievedChunk]
    suggest_case: bool
    safety: bool


def has_money(reply: AskReply) -> bool:
    text = f"{reply.headline}\n{reply.answer}".translate(ARABIC_DIGITS)
    return bool(MONEY.search(text) or GROUPED.search(text))


def run_ask(
    client: Completer, question: str, language: Language, law: Sequence[RetrievedChunk]
) -> AskResult:
    messages = ask_messages(question, language, law)
    reply = client.complete("ask", messages, AskReply)
    if reply.kind == "answer" and has_money(reply):
        log.warning("ask reply contained a money figure, retrying once")
        retry = correction(
            messages,
            reply.model_dump_json(),
            "the reply contains a money amount. Write no money amounts or currency figures; "
            "describe pay rules in words and days",
        )
        reply = client.complete("ask", retry, AskReply)
        if reply.kind == "answer" and has_money(reply):
            log.warning("ask reply still contained a money figure; answering unsure")
            reply = reply.model_copy(update={"kind": "unsure"})

    by_id = {chunk.id: chunk for chunk in law}
    cited = [by_id[cid] for cid in dict.fromkeys(reply.chunk_ids) if cid in by_id]
    kind: Kind = reply.kind
    if kind == "answer" and not cited:
        kind = "unsure"  # an answer the law we retrieved doesn't back is a guess
    safety = reply.safety or bool(DANGER.search(question))
    if kind != "answer":
        return AskResult(kind, "", "", [], reply.suggest_case, safety)
    return AskResult(kind, reply.headline, reply.answer, cited, reply.suggest_case, safety)
