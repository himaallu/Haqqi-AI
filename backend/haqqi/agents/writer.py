"""Writer agent: worker-language explanation + formal Arabic letter (task 3.10).

Ports Build/K2/Parse Writer. The model writes `[[AMOUNT_n]]` / `[[TOTAL]]` where money goes;
code fills in the calculator's figures. Output is rejected (one retry, then error) if the
letter's facts section has no Arabic or contains any amount (code prints the claims), a token
is unknown, or any figure next to a currency word is not one the calculator produced.
"""

import logging
import re
from decimal import Decimal, InvalidOperation

from haqqi.agents.messages import TOTAL_PLACEHOLDER, amount_placeholder, writer_messages
from haqqi.agents.schemas import AnalystReply
from haqqi.core.calculator import CalcResult, money
from haqqi.llm.client import Completer, LLMOutputError, Message
from haqqi.models import CaseFacts, WriterOutput

log = logging.getLogger(__name__)

ARABIC = re.compile(r"[؀-ۿ]")
TOKEN = re.compile(r"\[\[[A-Z_0-9]+\]\]")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٬٫", "0123456789,.")
_NUM = r"([0-9][0-9,]*(?:\.[0-9]+)?)"
_CUR = r"(?:AED|Dhs?\.?|dirhams?|درهم|دراهم|د\.إ)"
MONEY = re.compile(rf"{_CUR}\s*{_NUM}|{_NUM}\s*{_CUR}", re.IGNORECASE)
ANY_NUMBER = re.compile(_NUM)
# A figure that reads as money even without a currency word: 6,000 or 1500.50 (not dates).
GROUPED = re.compile(r"\d{1,3}(?:,\d{3})+|\d+\.\d{2}\b")
LETTER_FACTS = ("letter_facts_ar", "letter_facts_translation")


class WriterCheckError(ValueError):
    pass


def amounts_by_token(calc: CalcResult) -> dict[str, Decimal]:
    tokens = {
        amount_placeholder(i): line.amount_aed
        for i, line in enumerate(calc.claim, start=1)
        if line.amount_aed is not None
    }
    return {**tokens, TOTAL_PLACEHOLDER: calc.total_aed}


def allowed_figures(calc: CalcResult) -> set[Decimal]:
    """Every figure the calculator produced: amounts, the total, and numbers in its formulas."""
    figures: set[Decimal | None] = {calc.total_aed}
    for line in [*calc.claim, *calc.worker_owes]:
        if line.amount_aed is not None:
            figures.add(line.amount_aed)
        for text in (line.formula, line.note):
            figures.update(_to_decimal(n) for n in ANY_NUMBER.findall(text))
    return {money(f) for f in figures if f is not None}


def _to_decimal(text: str) -> Decimal | None:
    try:
        return Decimal(text.replace(",", ""))
    except InvalidOperation:
        return None


def fill_and_check(out: WriterOutput, calc: CalcResult) -> WriterOutput:
    if not ARABIC.search(out.letter_facts_ar):
        raise WriterCheckError("letter_facts_ar contains no Arabic text")
    for field in LETTER_FACTS:
        # A token here once stood in for the employer's own figure and reversed the meaning.
        text = getattr(out, field).translate(ARABIC_DIGITS)
        if TOKEN.search(text) or MONEY.search(text) or GROUPED.search(text):
            raise WriterCheckError(f"{field} contains an amount; the claims section lists them")
    tokens = amounts_by_token(calc)
    allowed = allowed_figures(calc)
    filled: dict[str, object] = {}
    for field, value in out.model_dump().items():
        texts = value if isinstance(value, list) else [value]
        done = [_fill(str(t), tokens) for t in texts]
        for text in done:
            _check_money(text, allowed, field)
        filled[field] = done if isinstance(value, list) else done[0]
    return WriterOutput.model_validate(filled)


def _fill(text: str, tokens: dict[str, Decimal]) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        if token not in tokens:
            raise WriterCheckError(f"unknown amount token {token}")
        return f"AED {tokens[token]:,.2f}"

    return TOKEN.sub(replace, text)


def _check_money(text: str, allowed: set[Decimal], field: str) -> None:
    for match in MONEY.finditer(text.translate(ARABIC_DIGITS)):
        figure = _to_decimal(match.group(1) or match.group(2))
        if figure is not None and money(figure) not in allowed:
            raise WriterCheckError(f"{field} contains a money figure not from the calculator")


def run_writer(
    client: Completer, facts: CaseFacts, reply: AnalystReply, calc: CalcResult
) -> WriterOutput:
    messages = writer_messages(facts, reply, calc)
    out = client.complete("writer", messages, WriterOutput)
    try:
        return fill_and_check(out, calc)
    except WriterCheckError as first:
        # The reason names a field and a rule, never the text itself.
        log.warning("writer output rejected, retrying once: %s", first)
        retry = [
            *messages,
            Message("assistant", out.model_dump_json()),
            Message(
                "user",
                f"Rejected: {first}. Write every amount only as its [[AMOUNT_n]] or [[TOTAL]] "
                "token, write no other money figures, write letter_facts_ar in Arabic, and put "
                "no amounts or tokens in letter_facts_ar or letter_facts_translation. "
                "Reply with ONLY the corrected JSON object.",
            ),
        ]
        out = client.complete("writer", retry, WriterOutput)
        try:
            return fill_and_check(out, calc)
        except WriterCheckError as second:
            raise LLMOutputError(f"writer: output rejected after one retry ({second})") from None
