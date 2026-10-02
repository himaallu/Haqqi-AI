"""Writer agent: worker-language explanation + formal Arabic letter (task 3.10).

Ports Build/K2/Parse Writer. The model writes `[[AMOUNT_n]]` / `[[TOTAL]]` where money goes;
code fills in the calculator's figures. Output is rejected (one retry, then error) if the
letter has no Arabic, a token is unknown, or any figure next to a currency word is not one
the calculator produced.
"""

import re
from decimal import Decimal, InvalidOperation

from haqqi.agents.messages import TOTAL_PLACEHOLDER, amount_placeholder, writer_messages
from haqqi.agents.schemas import AnalystReply
from haqqi.core.calculator import CalcResult, money
from haqqi.llm.client import Completer, LLMOutputError, Message
from haqqi.models import CaseFacts, WriterOutput

ARABIC = re.compile(r"[؀-ۿ]")
TOKEN = re.compile(r"\[\[[A-Z_0-9]+\]\]")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٬٫", "0123456789,.")
_NUM = r"([0-9][0-9,]*(?:\.[0-9]+)?)"
_CUR = r"(?:AED|Dhs?\.?|dirhams?|درهم|دراهم|د\.إ)"
MONEY = re.compile(rf"{_CUR}\s*{_NUM}|{_NUM}\s*{_CUR}", re.IGNORECASE)
ANY_NUMBER = re.compile(_NUM)


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
    # Check the model's own words: once tokens are filled, "درهم" would count as Arabic.
    if not ARABIC.search(TOKEN.sub("", out.arabic_letter)):
        raise WriterCheckError("arabic_letter contains no Arabic text")
    tokens = amounts_by_token(calc)
    allowed = allowed_figures(calc)
    filled: dict[str, object] = {}
    for field, value in out.model_dump().items():
        texts = value if isinstance(value, list) else [value]
        arabic = field == "arabic_letter"
        done = [_fill(str(t), tokens, arabic) for t in texts]
        for text in done:
            _check_money(text, allowed, field)
        filled[field] = done if isinstance(value, list) else done[0]
    return WriterOutput.model_validate(filled)


def _fill(text: str, tokens: dict[str, Decimal], arabic: bool) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        if token not in tokens:
            raise WriterCheckError(f"unknown amount token {token}")
        amount = f"{tokens[token]:,.2f}"
        return f"{amount} درهم" if arabic else f"AED {amount}"

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
        retry = [
            *messages,
            Message("assistant", out.model_dump_json()),
            Message(
                "user",
                f"Rejected: {first}. Write every amount only as its [[AMOUNT_n]] or [[TOTAL]] "
                "token, write no other money figures, and write arabic_letter in Arabic. "
                "Reply with ONLY the corrected JSON object.",
            ),
        ]
        out = client.complete("writer", retry, WriterOutput)
        try:
            return fill_and_check(out, calc)
        except WriterCheckError as second:
            raise LLMOutputError(f"writer: output rejected after one retry ({second})") from None
