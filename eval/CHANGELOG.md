# Evaluation changelog

Scores come from `make eval` (`eval/run_eval.py`). Before/after tables come from `python -m eval.compare BEFORE AFTER`,
which scores both runs on the same cases and re-scores hit@5 and "supported" against today's labels, so a label
change never counts as an improvement. `make eval EVAL_ARGS="--rescore --out <file>"` re-scores a saved run the same
way, with no LLM calls.

## 4 Oct 2026: CR 16 counts as a retrieval hit for unpaid wages (your call)

CR 1/2022 Art. 16(1) is the executive rule that wages are paid on their due date. It now counts as finding the right
law next to FDL Art. 22(2), in the key clauses of all 13 unpaid-wages cases. Both runs were re-scored, on the same 20
cases:

| Metric | Before | After | Target |
| --- | --- | --- | --- |
| Retrieval hit@5 | 60% | **92%** (12/13) | ≥ 90% |

The one miss left is TC-11: its top 5 has neither article. The Law Pack still gives the Analyst Art. 22. The table below
was scored before this label change.

## 4 Oct 2026: task 7.5, first fixes (K2, 20 of 50 cases)

Runs: `results/2026-10-04-k2.json` (before) and `results/2026-10-04-k2-after.json` (after).
- Model: K2. It is used for evaluation runs; production uses the free Gemini models.
- Cases: TC-01 to TC-21, all of the n8n set except TC-22 and TC-23. The other 30 run next (Gemini + K2 mix).

| Metric | Before | After | Target |
| --- | --- | --- | --- |
| Outcome accuracy | 100% | 100% | ≥ 95% |
| Issue detection | 100% | 100% | ≥ 85% |
| Retrieval hit@5 | 50% | **75%** | ≥ 90% |
| Citations cited | 100% | 100% | 100% |
| Citations supported | 98% | 96% | ≥ 90% |
| Critic catch rate | 100% (1/1) | 100% (1/1) | ≥ 90% |
| Calculator correctness | 100% | 100% | 100% |
| Injection resistance | 100% (1/1) | 100% (1/1) | 100% |
| Latency p95 (K2) | 223 s | 299 s | < 90 s |
| Cases lost to errors | 2 | 0 | 0 |
| Writer output rejected (results shown without it) | 0 | 2 | 0 |

What changed:
1. **K2 retry fix** (`a744769`). K2 rejects a conversation that re-sends its own reply as an assistant turn
   (HTTP 400), so every correction retry failed. In the first full run that was 16 of 50 cases. The retry is now one
   user turn that quotes the rejected reply. Before this fix, "before" lost 16 cases; with it, the 20 here lose none.
2. **Search query + issue words** (`bb2a456`). The law search adds plain law words for each issue the Intake found,
   for example "unpaid wages salary payment due date". Art. 1 (definitions) used to fill the top 5. hit@5 went from
   50% to 75%.
   - The 3 remaining misses are all unpaid-wages stories (TC-01, TC-10, TC-11). Art. 22(2) is outside the top 5,
     and CR 16(1) (wages paid on their due date) is often inside it.
   - In the app the unpaid-wages Law Pack always adds Art. 22, so the Analyst still cites it.
   - Since then, CR 16 counts as a hit (your call, see above).
3. **No breach the facts rule out** (CHANGES.md 27, `d469d1b`). The Analyst and Critic no longer flag notice when the
   full notice was served. In TC-21 the false Art. 43(2) finding is gone, and all its citations are now supported.
   Most of the cases this targets (N-03, N-09, N-11, N-12, N-18) are in the 30 still to run.
4. **Labels widened, documented in `d469d1b`.** Citations that are legally right but were missing from the hand
   labels now count:
   - CR 16 for unpaid wages;
   - Art. 51 + CR 30 when gratuity is claimed;
   - Art. 43 when the worker may owe notice;
   - Art. 65(6) for ending pre-2022 contracts.

   Re-scored this way, "supported" was already 98% before, so the earlier 83% mostly reflected the labels, not the
   model.

Not fixed:
- **Latency on K2** (p95 299 s): it is K2's speed, with some calls hitting the 90 s timeout. Gemini (production)
  took 12–49 s per case in the 6.3 language check.
- **Writer rejected on K2** in TC-02 and TC-04. The answer had no JSON after one retry. The page still shows the
  checked findings and amounts, with "Try again".
