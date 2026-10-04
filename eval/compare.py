"""Before/after metrics on the same cases (task 7.5): `python -m eval.compare BEFORE AFTER`.

Only cases present in both files are scored (errors included, so each side's error count shows).
"Supported" is re-scored on both sides against today's labels in cases.jsonl, so a label change
never shows up as an improvement. Prints a Markdown table for eval/CHANGELOG.md.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from eval.cases_io import load_cases
from eval.metrics import TARGETS, summarize


def load(path: Path) -> dict[str, Any]:
    cases: dict[str, Any] = json.loads(path.read_text())["cases"]
    labels = {c.id: c.expected.supporting_articles for c in load_cases()}
    for result in cases.values():
        if "citations" in result:
            result["violation_supported"] = [
                c.split(":cl")[0] in labels[result["id"]] for c in result["citations"]
            ]
    return cases


def fmt(key: str, value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{value:.0f} s" if key == "latency_p95_s" else f"{value * 100:.0f}%"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args()
    before, after = load(args.before), load(args.after)
    ids = [i for i in after if i in before]
    b = summarize([before[i] for i in ids])
    a = summarize([after[i] for i in ids])
    print(f"{len(ids)} cases: {', '.join(ids)}\n")
    print("| Metric | Before | After | Target |\n| --- | --- | --- | --- |")
    for key, target in TARGETS.items():
        name = key.replace("_", " ").replace("at 5", "@5").replace("p95 s", "p95")
        print(f"| {name} | {fmt(key, b.get(key))} | {fmt(key, a.get(key))} | {target} |")
    print(f"| errors (cases lost) | {b['errors']} | {a['errors']} | 0 |")
    print(f"| writer failed | {b['counts']['writer_failed']} | {a['counts']['writer_failed']} | 0 |")


if __name__ == "__main__":
    main()
