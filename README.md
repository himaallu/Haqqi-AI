# Haqqi (حقّي, "my right")

Haqqi is a multilingual UAE labour-rights assistant. A worker tells their story by voice or text in their own
language and gets:
- the rights that were likely broken, each citing an article of Federal Decree-Law 33/2021;
- an itemised claim from a deterministic calculator;
- a formal Arabic complaint to MOHRE, with a translation alongside.

Live: https://haqqi-ai.vercel.app. The full README (architecture, setup, demo) comes with task 8.9; see
`docs/PRD.md` and `docs/IMPLEMENTATION_PLAN.md` until then.

## Evaluation

These are the PRD metrics on the hand-labelled cases in `eval/cases.jsonl`, run with `make eval` (`eval/run_eval.py`).
Every expected amount is worked out by hand in `eval/CASES.md`. **This is a partial run: 20 of 50 cases** (TC-01 to
TC-21), measured on **K2**. Production uses free Gemini models. The remaining 30 cases come next. History is in
`eval/CHANGELOG.md`.

| Metric | Score | Target |
| --- | --- | --- |
| Outcome accuracy (analyse / refer / ask for info) | 100% | ≥ 95% |
| Issue detection | 100% | ≥ 85% |
| Retrieval hit@5 | 92% | ≥ 90% |
| Citations cited (from the retrieved law) | 100% | 100% |
| Citations supported (hand labels) | 96% | ≥ 90% |
| Critic catch rate (seeded bad citation) | 100% (1/1) | ≥ 90% |
| Calculator correctness | 100% | 100% |
| Injection resistance | 100% (1/1) | 100% |
| Latency p95 (K2) | 299 s | < 90 s |

The calculator check runs on every pull request without an LLM (`make eval-offline`): 40/40 hand-worked cases.
