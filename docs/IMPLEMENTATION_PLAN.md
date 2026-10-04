# Haqqi — Implementation Plan

Source of truth: docs/PRD.md. Rules: CLAUDE.md. Legacy: legacy/n8n/Haqqi_main.json (+ "Haqqi Test.json").
One sprint = one PRD block (~2 h). Tick boxes as tasks land. Each task: **Check** = how you verify it;
**Ports** = n8n node(s) it replaces ("new" = no n8n equivalent).

**n8n is a reference for intent, not a technical spec.** It shows what Haqqi should do. Its code, prompts and law
texts may contain mistakes. Any deviation from n8n is listed as a flag for approval before it is built.

## 0. Flags to resolve before Sprint 1

Legend: **BLOCKER** = decide before the sprint that needs it; **RISK** = plan around it; **NOTE** = minor fix.

### Product / legal
1. **BLOCKER (S3): free zones.** F2 says "free zone → redirect", Non-goals list only DIFC/ADGM/domestic, `CaseFacts.zone`
   has `free_zone`, and Open Questions says some free zones may follow federal law. n8n marks *every* free zone
   out of scope (Parse Intake + TC-14 JAFZA).
   **RESOLVED: smart referral.** DIFC and ADGM have their own employment laws and courts. Most other free zones broadly
   follow the federal law, but disputes go to the free zone authority first, not MOHRE, so the MOHRE complaint doesn't fit.
   v1 analyses **mainland only**. `zone` = `mainland | free_zone | difc | adgm`, plus `free_zone_name: str | None`.
   Referral text for DIFC/ADGM: "separate employment law; use the DIFC/ADGM courts". Referral text for other free zones:
   "federal gratuity rules broadly apply, but file with your free zone authority first". Both include MOHRE 80084.
   The model is ready to switch on free-zone analysis in v2.
2. **BLOCKER (S3): notice pay input.** `CaseFacts` has only `notice_given: bool`. n8n uses
   `notice_days_contract − notice_days_given` × total daily wage (Art. 43). Proposal: add `notice_days_contract`
   (default 30, clamp 30–90) and `notice_days_given` (default 0).
   **RESOLVED:** if a worker resigns without serving the contractual notice, show the notice pay they owe the employer
   (Art. 43(3)) as a separate, clearly labelled line. It is not subtracted from the worker's claim total unless decided otherwise.
3. **BLOCKER (S3): gratuity year convention.** n8n uses `(end−start)/365.25`. This makes *exactly one calendar year*
   0.9993 years, which is **ineligible**, and that breaks the PRD's "exactly 1 year" edge case.
   **RESOLVED: count whole days.** Service days = (end − start + 1 day) − unpaid absence days; years = days / 365;
   eligible if days ≥ 365. Exactly one calendar year qualifies.
4. **BLOCKER (S3): part-time gratuity.** The PRD requires a part-time test but gives no rule, and `CaseFacts` has no
   hours field.
   **RESOLVED:** add `weekly_hours`. In S2 we read the Executive Regulations' part-time gratuity article. If its rule is
   clear, gratuity is prorated by it (with tests). If not, the gratuity line says "not calculated: ask MOHRE".
   Every other line is calculated normally for part-time workers.
   *2 Oct, S2 finding:* CR 1/2022 Art. 30(1) is clear: part-time gratuity = (annual contract hours ÷ annual
   full-time hours) × the full-time gratuity. So we prorate. **RESOLVED (2 Oct, your choice):** the
   full-time base is 48 h/week (FDL Art. 17(1) maximum), so ratio = `weekly_hours ÷ 48`; the formula line states it.
5. **BLOCKER (S3): deductions and leave.** The PRD calculator table has no deduction rule, yet F4 lists "deductions".
   n8n refunds the *whole* reported deduction. Leave encashment is in the PRD but **not** in the n8n calculator.
   TC-22 (still employed, leave refused) expects total 0.
   **RESOLVED, deductions:** one claim line equal to every deduction the worker reports, citing Art. 25 and labelled
   "recoverable unless it falls under an allowed case in Art. 25". Deductions above 50% of the wage are flagged.
   **RESOLVED, leave:** paid out only when the job has ended: unused days × (basic ÷ 30). If the worker doesn't know
   the number of unused days, the line says "not calculated" rather than guessing. Still employed + leave refused →
   a violation (Art. 29) with no money line.
6. **RISK: unpaid absence days** (Art. 51(4)) are in the PRD rule but have no field. Proposal: add
   `unpaid_absence_days: int = 0`.
7. **RISK: 2-year limitation** (Art. 54(9)) is not in routing. Proposal: warn (not block) when `end_date` is more than 2 years ago.
8. **BLOCKER (S5): complaint identity fields.** The n8n letter keeps `[name] [labour card] [employer]` placeholders.
   The PRD says the letter is "ready to submit" but also "store only what the complaint needs".
   **RESOLVED:** ask for the three fields (optional) at download time, print them into the PDF, and never store or log them.
9. **RISK: "translation alongside"** needs an extra LLM call (Writer output → worker language) or a Writer schema
   change. It is not one of the 4 agents. Proposal: the Writer returns `letter_ar` + `letter_translation` in one call.
10. **NOTE: Arabic input.** The n8n form and TC-23 accept Arabic stories, but `CaseFacts.language` excludes `ar`.
    Proposal: allow `ar` as an input language (UI still offers the 7 + Arabic).
11. **NOTE: email and Sheets dropped.** Nodes `Log Stats` (Google Sheets) and `Email Case Pack` (Gmail) have no PRD
    equivalent. **RESOLVED:** stats move to Langfuse + a `cases` row, and email is dropped for v1.

### Data model
12. **BLOCKER (S3): nullable vs required.** `CaseFacts` makes `start_date` and wages required, but need-info routing
    needs them nullable.
    **RESOLVED:** `ExtractedFacts` (all optional + `issue_types`, `missing_info`, `facts_summary_en`, `in_scope`,
    `scope_reason`) → the worker confirms → strict `CaseFacts`.
13. **NOTE: missing fields.** Models lack `issue_types`, `contract_text`, `deducted_amount_aed`, notice days,
    `not_covered`, `documents_to_gather`, `time_limit_note`, critic verdict / `revised`, Writer output (`headline`,
    `amount_lines`, `checklist`, `arabic_letter`). `Emirate` enum and `Citation` are undefined. Map n8n
    `strength` (strong/moderate/weak) → PRD `confidence` (high/medium/low).
    **RESOLVED:** `CaseFacts` adds `issue_types`, `notice_days_contract`, `notice_days_given`, `deducted_amount_aed`,
    `unpaid_absence_days`, `weekly_hours`, `contract_text`, `unused_leave_days: int | None`, `free_zone_name`,
    and `ar` as an input language. `Analysis` adds `not_covered`, `documents_to_gather`, `time_limit_note`,
    `critic_verdict`, `revised`, and `worker_owes: list[ClaimLine]` (flag 2). `WriterOutput`, `CriticReport` and `Emirate`
    are defined in S3.
14. **BLOCKER (S2): citation id scheme.** n8n cites topic ids (`WAGES` = Art. 22 + 53). The PRD wants article-level
    `law_id/article_no/clause_no`.
    **RESOLVED:** chunk id `fdl33-2021:art51:cl2`; `Citation` = {chunk_id, law_id, article_no, clause_no, quote}. Law Pack
    topics map to lists of chunk ids. TC-11's bad citation is re-seeded as `fdl33-2021:art54:cl9`.

### Technical
15. **RISK: embedding model size.** BGE-M3 is about 2.3 GB and needs about 2 GB RAM. It won't fit free Render/Railway tiers or a
    fast CI.
    **REOPENED:** the backend moved to Render's free plan (512 MB), so BGE-M3 can't run there. Law vectors are still
    precomputed at ingest (any machine), and tests use a deterministic fake embedder. For query embeddings, task 2.5
    measures a quantised ONNX multilingual-e5-small in the running container. If it doesn't fit, the fallback is a
    free hosted embedding API, which sends query text off our server: **decision for you in Sprint 2.**
    **RESOLVED (2 Oct):** e5-small (int8 ONNX) peaks at about 520 MB per query batch (the dequantised 250k-token vocabulary),
    so it doesn't fit. IFM has no embeddings endpoint. You chose a free embeddings API: **BGE-M3 on Cloudflare Workers AI**
    (10k neurons/day ≈ 9M tokens, and no training on or reuse of content). Gemini's free tier was rejected because Google
    may use free-tier content to improve its products, including human review.
16. **RISK: Arabic full-text search.** "BM25-style" in Postgres is really `ts_rank`. Arabic stemming needs the `arabic`
    text-search config on Supabase/Neon, so verify it in S2. Fallback: `simple` config on normalized Arabic (strip tashkeel).
    *2 Oct:* confirmed on Supabase. Migration 0001 builds `tsv_ar` with `to_tsvector('arabic', …)`, and it applied cleanly.
17. **RISK: Arabic PDF extraction.** Official Arabic PDFs often extract with broken glyph order. n8n already notes
    Art. 17(1) failed to extract. Budget time and keep a hand-corrected `data/law/*.json` as the canonical source.
    The ingest script reads the JSON, and the PDFs are provenance only.
    *2 Oct:* avoided. The parser reads the portal's HTML text (EN + AR), which has clean Arabic, so no hand fixes are needed.
18. **RISK: latency < 90 s p95.** *2 Oct:* K2: one real case took 153 s (calls 5–77 s each). **Gemini
    (`gemini-3-flash-preview`): the same TC-02 case took 13 s** (intake 2, analysis + critic 5, writer 6). Free-tier limit:
    **5 requests/minute** per model, and a case needs 4–6 calls, so a second case in the same minute falls back to K2 (slow).
    *3 Oct:* quotas are per model, so the client chains the free models before K2: 3-flash-preview (5/min) →
    3.5-flash (5) → 3.8-flash (5) → 3.1-flash-lite (15), about 30 requests/min in all (`GEMINI_FALLBACK_MODELS`).
    A 429 moves straight to the next model instead of waiting out the ~40 s quota window.
    **4 Oct: the free tier also caps each model at 20 requests per day** (429 `GenerateRequestsPerDayPerProjectPerModel`).
    At 4–6 calls per case that is about 10–12 cases a day on the three Flash models, then Flash-Lite, then K2 (slow).
    The client now parks a model for the wait Google asks for (capped at 1 h), so later calls skip it.
    **RISK for Sprint 7:** the 50-case eval needs 200–300 calls: spread it over days, run it on K2, or enable billing for it. There are 4–5 sequential K2 calls, and n8n used 180 s timeouts × 3 retries. Measure in S3
    and set per-call timeouts (e.g. 40 s, 1 retry). v1 has no backup LLM (see 0.1): the client keeps a provider slot
    so one can be added later, and a K2 outage shows a clear "try again later" message.
19. **RISK: streaming through hosting.** SSE for 60–90 s must not pass through a Vercel serverless function, because it would time out.
    The browser should call the backend directly (CORS allow-list), and Render's request timeout must be checked.
20. **RISK: K2 key validity / rate limits** (PRD open question). K2's weights are open, so a self-hosted copy has no central
    rate limit. We use IFM's *hosted* API (`api.ifm.ai`) with a key, though, and that has its own limits. Self-hosting the 375B model
    isn't possible for free. Task 1.9 tests the key. If it fails, a backup provider is chosen.
    **RESOLVED (2 Oct, task 1.9):** the K2 key works (reply in 1.75 s). Limits from the response headers:
    **2 requests/second** and **10M tokens per 24 h**. Fine for 4–5 sequential calls per case; the client
    must not fire calls in parallel and should back off on HTTP 429.
21. **NOTE: 7-day auto-delete** isn't in any block. Added to S8 as a scheduled purge.
22. **NOTE: CI and the network.** `make eval` needs K2, so CI runs only the calculator + retrieval subset offline.
    "Ingest runs in CI" needs the law JSON committed (small) rather than downloading PDFs.
23. **NOTE: repo facts.** **RESOLVED:** `CLAUDE.md` moved from `docs/` to the repo root so Claude Code loads it, and its
    reference to the test file now uses the real name `Haqqi Test.json`.
    The PRD says "12 hackathon cases", but the harness has **22** (TC-01–12, TC-14–23; no TC-13). Port all 22.
24. **NOTE: metrics definitions.** "≥ 90% supported" citations and the resume's "faithfulness" need a method
    (LLM-judge vs hand labels). Proposal: hand-label `supported` per expected article in cases.jsonl; LLM-judge is optional.
25. **RISK: schedule.** 8 × 2 h blocks for this scope is very tight. Follow the PRD cut order. Sprint 3 is the biggest; split
    its agent work into 3a (calculator/routing, no LLM) and 3b (agents) so the deterministic core lands even if K2 is down.
26. **DECISION (2 Oct): Gemini free tier for the LLM.** You chose free-tier Gemini (with K2 as fallback) to cut latency.
    Google's terms say free-tier content may be used to improve its products and read by human reviewers. That deviates
    from the PRD's "no training on user data". Mitigations:
    - The story screen tells workers not to include names, phone numbers, passport, Emirates ID or labour card numbers (S4, task 4.3).
    - The results page and disclaimer say the text is processed by Google Gemini (S8, task 8.7).
    - Billing can be enabled later to move to the paid tier, which doesn't use data for training, without a code change.
    - **3 Oct, your choice: free tier only.** Billing stays off in AI Studio; extra capacity comes from chaining free models (flag 18).

## 0.1 Free stack (replaces the PRD's paid choices)

Everything runs on free tiers. Check each tier's limits **and data-use terms** at signup. Some free tiers may use the
data sent to them for training, which would break the PRD's "no training on user data". Record the result in `docs/SERVICES.md`.

| Area | Free choice | Notes |
| --- | --- | --- |
| Frontend | Vercel Hobby | Preview deploys per PR |
| Backend | Render free web service (Docker) | `render.yaml` Blueprint builds `backend/Dockerfile`; 512 MB RAM; sleeps after ~15 min idle (~1 min cold start). Hugging Face was dropped: free accounts can no longer use CPU-basic Spaces |
| Database | Supabase free (Postgres + pgvector) | Pauses after inactivity; Neon free as alternative |
| Embeddings | Cloudflare Workers AI, BGE-M3 (flag 15) | 10k neurons/day free; no training on content; ingest and queries use the same model |
| Speech | Cloudflare Workers AI, Whisper large-v3-turbo (your choice, 4 Oct) | Same account and free allowance as the embeddings; no training on content; the worker's language is sent as a hint (it decides Hindi vs Urdu script) |
| LLM | Gemini free tier only (`gemini-3-flash-preview`, then free 3.5-flash, 3.8-flash, 3.1-flash-lite), K2 as fallback (user decision, 2 Oct) | K2 made one case take 153 s, so Gemini is now primary. Free tier: 5 requests/minute and 20/day per model (flag 18), and Google may use the data (flag 26). `LLM_PROVIDER=k2` reverses the order |
| PDF | WeasyPrint + Noto Naskh Arabic | Open source |
| Tracing / errors | Langfuse Cloud Hobby / Sentry free | PII redacted before sending |

## Sprint 1 — Skeleton (PRD Block 1)

- [x] **1.1 Monorepo layout**: `backend/` (haqqi/api, core, rag, pdf, tests), `frontend/`, `eval/`, `data/law/`,
      `.github/workflows/`.
      Check: `tree -L 2` matches the PRD layout. Ports: new.
- [x] **1.2 Backend scaffold**: FastAPI app, `pyproject.toml` (Python 3.12, fastapi, pydantic v2, httpx, pytest, ruff, mypy),
      `GET /healthz` returning `{status:"ok", db:"ok|down"}`.
      Check: `curl localhost:8000/healthz` → `{"status":"ok",...}`; `pytest` has 1 passing test. Ports: new.
- [x] **1.3 Settings**: `pydantic-settings` config (`K2_API_KEY`, `K2_BASE_URL`, `DATABASE_URL`, …) and `.env.example`.
      Check: the app boots with `.env.example` values copied; `git grep -i "sk-\|api_key="` finds no secrets. Ports: `K2 Horizon API` credential.
- [x] **1.4 Frontend scaffold**: Next.js App Router + TS + Tailwind + shadcn/ui, managed with **pnpm**
      (`pnpm-lock.yaml` committed; `packageManager` pinned in `package.json`), with a page that fetches `/healthz`.
      Check: `pnpm install --frozen-lockfile && pnpm build` passes; the page shows "backend: ok". Ports: new.
- [x] **1.5 docker-compose**: `db` (pgvector/pgvector:pg16), `backend`, `frontend`.
      Check: `make dev` → all 3 healthy; `psql -c "create extension vector"` succeeds. Ports: new.
- [x] **1.6 Makefile**: `dev`, `test`, `lint`, `eval` (stub).
      Check: `make test && make lint` exit 0. Ports: new.
- [x] **1.7 Deploy hello-world**: frontend to Vercel, backend to Render via `render.yaml`, DB on Supabase (see 0.1).
      Check: the public frontend URL shows "backend: ok" from the public backend. Ports: new.
      *Done 2 Oct:* https://haqqi-ai.vercel.app shows `backend: ok · db: ok` from https://haqqi-api.onrender.com.
- [x] **1.8 Minimal CI**: GitHub Action runs `make lint` and `make test` on PRs.
      Check: a PR shows green checks. Ports: new.
- [x] **1.9 LLM key smoke test**: `python -m haqqi.llm.smoke` sends one chat call to K2 and one to Groq. It prints
      latency and any rate-limit headers, never the key.
      Check: both return a reply, or the failure is recorded in flag 20 and Groq is made primary. Ports: `K2 Horizon API` credential.
      *Done 2 Oct:* K2 OK (1.0–1.75 s; 2 req/s, 10M tokens/day). Groq: HTTP 404 "model does not exist or you do
      not have access to it", so the key has no free model access. Decision: K2 only for v1 (flags 18 and 20).

## Sprint 2 — Knowledge base (PRD Block 2)

- [x] **2.1 Law Pack → data**: extract the 10 Law Pack entries (English text, refs, topics) into `data/law/law_pack.json`,
      re-keyed to article-level chunk ids (flag 14), plus the `RELATED` and `ALWAYS` topic maps.
      Check: a unit test loads 10 topics; every topic maps to ≥ 1 chunk id; Art. 51 text matches the official source text (n8n text may be wrong). Ports: `Law Pack`.
      *2 Oct:* `data/law/law_pack.json` (10 topics, related, always) + provisional `data/law/fdl33-2021.json` (44 chunks
      from the n8n texts). Tests pass; the Art. 51 check against the official text waits for task 2.2's download.
      *Done 2 Oct:* the official file replaces the provisional one. Every n8n clause text matches the official English
      (similarity ≥ 0.9), and every pack id resolves. Gratuity adds CR 1/2022 Art. 30 (part-time), and leave adds CR Art. 19(2).
- [x] **2.2 Source download + provenance**: fetch FDL 33/2021, CR 1/2022 and FDL 20/2023 (EN + AR) and MOHRE pages;
      record URL + retrieval date in `data/law/SOURCES.md`.
      Check: SOURCES.md lists every file with a URL and date. Ports: `Setup` note, step 3.
      *Done 2 Oct:* the consolidated FDL 33/2021 text (it already includes FDL 20/2023) and CR 1/2022, EN + AR, saved
      from uaelegislation.gov.ae via Firecrawl (Cloudflare blocks curl), each with a sha256. MOHRE pages are unreachable
      for now and listed as "not yet fetched"; they are not law text and are needed only in S8.
- [x] **2.3 Article parser**: PDF/HTML → `data/law/<law_id>.json` (one record per article, split by clause, EN/AR side by side),
      with hand fixes committed (flag 17).
      Check: `pytest tests/rag/test_parse.py`; Art. 51 has 8 clauses; Arabic text of Art. 51 is readable (eyeball 3 articles). Ports: new.
      *Done 2 Oct:* `python -m haqqi.rag.parse` gives FDL 33/2021 (74 articles, 253 chunks) and CR 1/2022 (39 articles, 122 chunks).
      EN and AR clause counts match for every article. A drift test keeps the JSON in sync with the raw files.
      Eyeballed Art. 51(2), 53, 54(9) and 43(3), plus CR 30(1).
- [x] **2.4 Schema + migrations**: `law_chunks(id, law_id, article_no, clause_no, title, topic_tags[], text_en, text_ar,
      source_url, effective_date, embedding vector, tsv_en, tsv_ar)` plus a `cases` table.
      Check: `alembic upgrade head` on a fresh DB; `\d law_chunks` shows the vector + GIN indexes. Ports: new.
      *Done 2 Oct:* untyped `vector` column (model-agnostic) and no vector index (exact search over a few hundred rows);
      GIN indexes on `tsv_en`, `tsv_ar` (Postgres `arabic` config works, flag 16) and `topic_tags`. `make db` = migrate + ingest.
- [x] **2.5 Embedder interface** (flag 15): the `Embedder` protocol, a local open-model implementation, and a deterministic fake for tests.
      Check: a unit test with the fake embedder; the local model embeds one Hindi and one Arabic sentence with the expected
      dimension, and memory stays within the host's limit. Ports: new.
      *2 Oct:* `Embedder` protocol + deterministic `HashEmbedder` done and tested; the real model needs huggingface.co
      (network change requested), then the 512 MB measurement decides flag 15.
      *2 Oct:* `CloudflareEmbedder` (BGE-M3, 1024-d, batches of 50, normalised) done, with mocked HTTP tests. Dense search
      skips stored vectors of another dimension. Waiting on your Cloudflare account ID + token to run the live
      Hindi/Arabic test (`make test-live`).
      *Done 2 Oct:* the live test passes: Hindi and Arabic each land closest to the English equivalent, 1024-d. Requests are
      capped by size as well as count (Cloudflare allows 60k tokens per request). A full ingest of 375 chunks takes about 14 s.
      Memory is not a concern because the model is hosted.
- [x] **2.6 `python -m haqqi.ingest`**: rebuilds the index from `data/law/*.json` idempotently.
      Check: run it twice → same row count; `select count(*) from law_chunks` ≈ articles × clauses. Ports: new.
      *Done 2 Oct:* two runs → 44 rows each (provisional data); rebuild is one transaction.
      *2 Oct:* Supabase migrated (`0001`) and indexed with `EMBEDDER=cloudflare`: 375 chunks (run from the laptop; this
      sandbox can't reach Postgres on 5432).
- [x] **2.7 Hybrid retrieval**: dense (pgvector cosine) + FTS (EN + AR config, flag 16) → RRF (k=60) → top 8, merged
      with Law Pack chunks for the intake `issue_types` (+RELATED, +ALWAYS).
      Check: `pytest tests/rag/test_retrieve.py` (a fake-embedder test proves RRF ordering and pack merge). Ports: `Law Pack` (topic selection).
      *Done 2 Oct:* RRF + pack-merge unit tests, plus a live Postgres test (gratuity query → Art. 51 first, Art. 54(9) always included).
- [x] **2.8 Eyeball 10 queries**: `python -m haqqi.rag.probe "<query>"` for 10 queries in EN/HI/AR, results saved to
      `eval/retrieval_probe_<EMBEDDER>.md`.
      Check: at least 8/10 have the expected article in the top 5 (by eye). Ports: new.
      *2 Oct:* `python -m haqqi.rag.probe` (one query, or `--all` → `eval/retrieval_probe_<EMBEDDER>.md`), search only
      with no pack top-up. Keyword-only baseline (hash embedder): **5/10**. Hindi and paraphrased English miss. The BGE-M3
      run follows once the Cloudflare token is set.
      *Done 2 Oct:* BGE-M3 hybrid scored **7/10**. Full-text search then changed from all-words (AND) to any-word (OR),
      still ranked by `ts_rank`, which gave **8/10** (`eval/retrieval_probe_cloudflare.md`). Remaining misses: "salary unpaid"
      in HI/AR should find Art. 22(2), but search alone doesn't reach it. In the real flow the `unpaid_wages` Law Pack adds Art. 22,
      and Sprint 3 queries with the Intake's English summary.

## Sprint 3 — Core logic (PRD Block 3)
*(3a = tasks 3.1–3.4: no LLM, runs even if K2 is down. 3b = tasks 3.5–3.11: agents.)*

- [x] **3.1 Pydantic models**: `ExtractedFacts`, `CaseFacts`, `Citation`, `Violation`, `ClaimLine`, `Analysis`,
      `CriticReport`, `WriterOutput`, `Emirate` (flags 12–13). Money fields are `Decimal`.
      Check: `mypy --strict haqqi/core haqqi/models.py`; a round-trip JSON test. Ports: the JSON contracts in `Build * Prompt` nodes.
      *Done 2 Oct:* `haqqi/models.py`; strict `CaseFacts` validates basic ≤ total, end date vs termination, no extra keys.
      Added `deducted_monthly_aed` (optional) so the Art. 25(2) 50% check compares like with like; `ClaimLine.amount_aed`
      is `None` for "not calculated" lines.
- [x] **3.2 Calculator** `haqqi/core/calculator.py`: gratuity (Art. 51, eligibility, 21/30 days, 2-year cap, unpaid absence),
      unpaid wages, notice pay, notice pay owed *by* a worker who resigned without notice (separate line, flag 2),
      deductions refund, leave encashment, `above_mohre_limit` (50,000), each with `formula` +
      `Citation`. Constants live in one `CONFIG` block and Decimal rounding is ROUND_HALF_UP to 0.01. Rules follow flags 2–6.
      Check: `pytest tests/core/test_calculator.py` → 100%, covering hand-worked TC-01 and TC-03 plus exactly-1-year,
      exactly-5-years, cap-hit (TC-20), part-time, still-employed (no gratuity), and TC-21. Calculations are written out in
      `tests/core/CASES.md`. Ports: `Calculator`.
      *Done 2 Oct:* 23 tests, all matching hand-worked figures in CASES.md. Every line cites a real clause, and `cite()` rejects
      unknown ids. Decisions: flexible contracts → gratuity "not calculated, ask MOHRE"; an under-one-year gratuity shows
      0.00 with the reason. TC-21 is 18,381.37 under the whole-day rule; n8n's `max_total` 18,366 used ÷365.25, so the
      Sprint 7 eval row uses our figure.
- [x] **3.3 Routing** `haqqi/core/routing.py`: out_of_scope (free zone/DIFC/ADGM/domestic by form or story), need_info
      (no wage or no start date), ready. The form overrides the model.
      Check: table test with TC-07, 08, 09, 14, 15, 16, 17 → expected route. Ports: `Parse Intake` (override + critical_missing), `Route Case`.
      *Done 2 Oct:* `route_case(extracted, form_zone, form_worker_type)`. The form answer wins over the model in both directions
      ("not sure" falls back to the model). Referral texts for domestic, DIFC/ADGM and free zone include 80084. The table covers TC-01/07/08/09/14/15/16/17.
- [x] **3.4 Input normalisation**: a request schema with length limits; the story is wrapped in `<<<WORKER_DATA>>>` delimiters.
      Check: an 8,001-char story → 422; a unit test shows the delimiter wrapping. Ports: `Normalize Input`.
      *Done 2 Oct:* `haqqi/api/schemas.py` `CreateCaseRequest` (story 1–8,000 chars, contract ≤ 4,000, wage bounds, no extra
      keys; control/bidi characters stripped). `haqqi/core/untrusted.py` `wrap_worker_data` removes any copy of the delimiters
      from inside the story, so it can't close the fence early.
- [x] **3.5 K2 client** `haqqi/llm/client.py`: OpenAI-compatible httpx client that strips `<think>` and fences, parses into a
      Pydantic model, retries once on invalid JSON then raises `LLMOutputError`, uses per-call timeouts, and has a fallback-provider
      hook (flag 18).
      Check: unit tests with recorded responses (valid, fenced, think-tag, invalid×2 → error). Ports: `K2 Intake/Analyst/Critic/Revise/Writer` (HTTP) + the `parseK2` function.
      *Done 2 Oct:* `LLMClient.complete(stage, messages, schema)`. Parsing: strips `<think>` and fences, keeps the outer object,
      Pydantic. Bad output gets one correction retry, then `LLMOutputError`. Transport: 40 s timeout, one retry on 5xx or
      timeout, 429 honours Retry-After, next provider, then `LLMUnavailable`. Calls are serialised with a 0.5 s gap
      (2 req/s) at temperature 0. Logs show only stage, latency and token counts. 10 tests.
      *3 Oct:* free-tier Gemini first (one provider per free model, flag 18), then K2; a 429 moves to the next model.
- [x] **3.6 Prompts** `haqqi/rag/prompts/*.md`: the Intake, Analyst, Critic, Revision and Writer prompts, starting from the n8n
      prompts and rewritten where needed. Each material change is recorded in `haqqi/rag/prompts/CHANGES.md` for review.
      Arabic letter template in `haqqi/pdf/template_ar.txt`.
      Check: you review and approve CHANGES.md; prompt snapshot tests pass. Ports: `Build Intake/Analyst/Critic/Revision/Writer Prompt`.
      *2 Oct:* the prompts, the message builders (`haqqi/agents/messages.py`) and the Arabic template are written, with 12 snapshot
      and safety tests (one fence per message, the writer sees money only as `[[AMOUNT_n]]`). *Done 3 Oct:* you approved
      `haqqi/rag/prompts/CHANGES.md`.
- [x] **3.7 Intake agent** → `ExtractedFacts`.
      Check: `pytest -m live tests/agents/test_intake.py` on TC-01 (Hindi) → `unpaid_wages`, wage 1800; TC-18 fills
      dates and wages from the story. Ports: `Build Intake Prompt`, `K2 Intake`, `Parse Intake`.
      *Done 2 Oct:* `run_intake` (the form's answers then override the model's). Live K2: TC-01 → unpaid_wages, total 1800,
      3 months unpaid, still employed; TC-18 → start 2025-05-01, total 2200, basic 1600. About 8 s per call.
- [x] **3.8 Citation enforcement**: drop article ids that are not in the retrieved ∪ pack set, and move uncited findings to `not_covered`.
      Check: a unit test with a fabricated id → removed and finding moved. Ports: `enforceCitations` in `Parse Analyst`/`Parse Revision`.
      *Done 2 Oct:* `enforce_citations` + `to_violations` (quotes come from our law text, never the model). 2 unit tests.
- [x] **3.9 Analyst → Critic → one revision**, plus a test-only `force_bad_citation` hook (enabled only by an env flag).
      Check: live TC-11 → critic `revise`, `revised=True`, final citation ≠ Art. 54(9). A unit test with mocked LLM
      proves at most one revision. Ports: `Build/K2/Parse Analyst`, `Build/K2/Parse Critic`, `Critic Passed?`, `Build/K2/Parse Revision`.
      *Done 2 Oct:* `run_analysis` enforces citations after every reply. Seeding only happens when the caller passes it, and
      the API passes it only when `HAQQI_TEST_HOOKS=1`. Live TC-11: critic `revise` → one revision → Art. 54(9) gone.
      3 calls took 7 + 11 + 5 s. 3 unit tests use a scripted fake LLM.
- [x] **3.10 Writer agent** → `WriterOutput` (worker-language text + Arabic letter + translation, flag 9). Rejects output with no
      Arabic script, and amounts are injected from the calculator, never the LLM.
      Check: live TC-03 → `arabic_letter` matches `[؀-ۿ]`; every AED figure in the text equals a calculator figure (regex test). Ports: `Build Writer Prompt`, `K2 Writer`, `Parse Writer`.
      *Done 2 Oct:* `run_writer` fills `[[AMOUNT_n]]`/`[[TOTAL]]` from the calculator. One retry, then an error, if the letter
      has no Arabic (checked before filling), a token is unknown, or any figure next to AED/درهم (Arabic-Indic digits too)
      is not a calculator figure. Live TC-03 passed (35 s; 3.8k output tokens). 7 unit tests.
- [x] **3.11 Orchestrator + API**: `POST /v1/cases`, `PATCH /v1/cases/{id}`, `POST /v1/cases/{id}/analyze` (SSE events:
      `retrieving`, `calculating`, `analysing`, `critiquing`, `revising`, `writing`, `done`). Case ids are UUIDv4.
      Check: `curl -N` shows ordered stage events, then an `Analysis` JSON; TC-07 returns a referral with no violations. Ports: the `connections` graph; `Assemble Case Pack`; `Out-of-Scope Reply`; `Need-Info Reply`.
      *Done 2 Oct:* `haqqi/api/cases.py` + `haqqi/agents/pipeline.py`. Cases are stored in `cases` (story kept only for analysis;
      7-day expiry). Out-of-scope returns the referral with no LLM analysis. LLM failures stream an `error` event with a
      "try again later" message. 4 API tests (scripted LLM + local DB) + 2 pipeline tests.
      Real run, TC-02 (Urdu, local server, K2 + BGE-M3): total 6,229.59 = CASES.md. Citations Art. 42(3), 43(1/3/4), 51(2/3/5).
      **Latency 153 s:** intake 9, analyst 77 (40 s timeout + retry), critic 32, writer 34. The per-call timeout is now 90 s
      (flag 18). **Quality:** the letter wrote the end date as 2024 instead of 2026, to fix in the Sprint 7 eval loop.
      *2 Oct, Gemini:* the same TC-02 run took 13 s end to end; total 6,229.59, citations Art. 42(3), 43(1/3), 51(2/3),
      and the letter dates are correct (2024-06-01 → 2026-09-20). Live agent tests pass on Gemini.

## Sprint 4 — UI flow (PRD Block 4)

- [x] **4.1 i18n setup**: 7 languages + Arabic UI strings (JSON catalogs, RTL for ur/ar).
      Check: switching to Urdu flips `dir="rtl"`; no missing-key warnings in the console. Ports: new.
      *Done 3 Oct:* `frontend/lib/i18n/` holds 8 JSON catalogs (no library) with `t()`, which falls back to English and warns
      on a missing key. A test keeps every catalog on the English key set and placeholders. The non-English catalogs are
      **drafts for native review in 6.3**. `/ur` and `/ar` set `dir="rtl"` on the page and on `<html>`. Noto fonts per script
      (Nastaliq for Urdu) are self-hosted via `next/font`. No console warnings during the browser run.
- [x] **4.2 Language picker** (flags + native script).
      Check: at 375 px wide, all 8 options are tappable (≥ 44 px). Ports: `Haqqi Form` (Preferred language).
      *Done 3 Oct:* at 375 px, the 8 options are 343 px wide and 58–82 px tall, with no horizontal scroll (`docs/screens/s4-picker.png`).
- [x] **4.3 Story input** (text; mic button stubbed for S6), with the "don't include name/ID/passport" hint.
      Check: submitting calls `POST /v1/cases` and moves to the confirm step. Ports: `Haqqi Form` (Your story, description).
      *Done 3 Oct:* 8,000-char counter, privacy hint, Gemini notice (flag 26), mic stub. Submit → `/{lang}/case/{id}`.
- [x] **4.4 Confirm-fields form**: emirate, zone, worker type, contract type, dates, wages, months unpaid, notice days,
      leave days, pre-filled from extraction and marked "please confirm".
      Check: TC-18 story → fields pre-filled; editing a field calls `PATCH`; the need-info route highlights missing fields. Ports: `Haqqi Form` fields, `Need-Info Reply`.
      *Done 3 Oct:* TC-18 pre-fills Ajman, 2025-05-01, 2,200/1,600, still employed (7 "please confirm" badges).
      TC-02 (Urdu, story only) → need-info banner + 3 highlighted fields. The PATCH sends every field (hidden ones as null),
      digits typed on Arabic/Indic keyboards are accepted, and 422s map back to fields. New backend (your choice):
      `GET /v1/cases/{id}` so a reload resumes the case; `CaseView` adds `referral_kind` and `missing_fields`.
- [x] **4.5 Progress view** consuming SSE.
      Check: stages tick live during a real run. Ports: new (F8).
      *Done 3 Oct:* fetch-based SSE reader (POST). Real TC-02 run: the stages ticked at 0.1 / 0.9 / 8.2 / 17.9 s → results at 23.9 s.
- [x] **4.6 Results page**: verdict + violations with article citations (expandable quote), itemised claim with
      formulas, total, a separate "you may owe your employer" notice line (flag 2), above-50k note, next steps, documents, not-covered notice, disclaimer (EN + worker language + AR, MOHRE 80084).
      Check: TC-02 shows termination + notice with citations; every amount row shows a formula. Ports: `Assemble Case Pack` (page_html).
      *Done 3 Oct:* TC-02 in Urdu → Art. 43(1), 43(3), 42(3), 44(2), 51(2), 51(3); notice pay 3,000.00 + gratuity 3,229.59
      = **6,229.59** (CASES.md), each with its formula. A reload shows the saved result. The analyst's findings, formulas, documents and law quotes
      are English (labelled "shown in English"); the Writer's headline, explanation, amount lines and checklist are in
      the worker's language. To review in 6.3: translating the analyst fields.
- [x] **4.7 Referral page** for out-of-scope cases, with three texts: domestic worker, DIFC/ADGM, other free zone (flag 1).
      Check: TC-08 → domestic referral; TC-07 (DIFC) → DIFC/ADGM referral; TC-14 (JAFZA) → free-zone-authority referral. Ports: `Out-of-Scope Reply`.
      *Done 3 Oct:* TC-08 (ne) → domestic, TC-07 → difc_adgm, TC-14 → free_zone, each with a tap-to-call 80084.
- [x] **4.8 Deploy + phone run**.
      Check: one full case completed on a real phone against the public URL; screenshot saved to `docs/screens/`. Ports: `Show Result`.
      *4 Oct, first phone run (iPhone, Safari):* every analysis failed with "Something went wrong" at `retrieving`. The
      Docker image held only `backend/`, so `data/law/*.json` (law text + Law Pack) was missing on Render. Fixed: the image
      builds from the repo root, copies `data/law/*.json`, and fails to build if they don't load (`LAW_DATA_DIR`); Render
      redeploys on `data/law/**` changes. The rebuilt container ran TC-02 (English) end to end: 6,229.59.
      Also found: the Intake guessed 2024 for "20 September" (it now gets today's date; CHANGES.md 21,
      approved 4 Oct), iOS date inputs overflowed the card (CSS fix), and `/healthz` showed `dev` (now `RENDER_GIT_COMMIT`).
      *Done 4 Oct, second phone run:* English TC-02 on the public URL → **6,229.59**, Art. 43(1)/43(3)/42(3)/51(2), formulas
      shown (`docs/screens/s4-phone-results-en.jpeg`). The first attempt failed at the Writer ("could not check";
      `s4-phone-writer-error-en.jpeg`), most likely a weaker fallback model after the daily quotas ran out (flag 18).
      Follow-ups (your choice: show results anyway): a Writer failure now returns the checked findings and amounts with a
      notice and "Try again" (`writer_failed`); rejection reasons are logged; models over their daily quota are parked;
      one card per finding with all its articles; the gratuity formula drops the 30-day term under 5 years.

## Sprint 5 — Arabic complaint (PRD Block 5)

- [x] **5.1 PDF smoke test first**: WeasyPrint + Noto Naskh Arabic in the Docker image renders a fixed Arabic paragraph.
      Check: `make pdf-smoke` → `out/smoke.pdf`; letters are joined and RTL (open and look); `pdffonts` shows NotoNaskhArabic. Ports: new.
      *Done 3 Oct:* the Noto fonts (Naskh Arabic, Nastaliq Urdu, Devanagari, Malayalam, Bengali, Sans; OFL, about 4.6 MB)
      are committed in `haqqi/pdf/fonts/`, so every machine renders the same glyphs. The image installs Pango/HarfBuzz and
      **fails to build** if the smoke PDF doesn't embed Naskh. The script lists the embedded fonts itself (the image has no
      poppler `pdffonts`). Letters joined and RTL (checked by eye). Peak memory is 62 MB in the image, well under Render's 512 MB.
- [x] **5.2 HTML/Jinja template**: the n8n TEMPLATE_AR sections (to MOHRE, subject, worker data, facts, legal basis, claims,
      requests, attachments, date/signature) with Arabic on one side and the translation on the other.
      Check: a golden-file test on the rendered HTML; the PDF of TC-03 is visually OK. Ports: `TEMPLATE_AR` in `Build Writer Prompt`.
      *Done 3 Oct:* `haqqi/pdf/letter.html.j2` + `letter.py`. Arabic is on the right and the worker's language on the left;
      Arabic-language cases get one column. Fixed text lives in `haqqi/pdf/strings/<lang>.json`. The non-English catalogs
      are **drafts for native review in 6.3**. Golden HTML for TC-03 in en, ur and ar (`UPDATE_GOLDEN=1` to refresh). A test
      checks that each script's font is embedded; it caught Urdu falling back to Naskh. Your choices: references only
      (no clause quotes), and the worker-owes line is left out of the complaint.
- [x] **5.3 Deterministic fill**: claims and amounts come from the calculator, articles from the citations, and prose (facts section)
      from the Writer.
      Check: a test proves every number in the PDF text equals a `ClaimLine.amount_aed`. Ports: `Build Writer Prompt` (claims rule).
      *Done 3 Oct:* the Writer now returns only `letter_facts_ar` + `letter_facts_translation` (CHANGES.md 22, **for your
      review**); code builds the rest. The PDF text test checks every money figure is a claim amount, the total, or a
      confirmed wage (wages come from the form, not the calculator, and the worker data block prints them). The
      first live TC-03 run showed why the facts section must carry **no amounts**: the claim token stood in for the employer's
      offer, so the letter said the employer offered 16,056.85. Code now rejects any amount or token there (one retry).
- [x] **5.4 Identity fields at download** (flag 8): name, labour card and employer are rendered but never stored or logged.
      Check: after download, a DB row check and log grep show none of the 3 values. Ports: placeholders in `TEMPLATE_AR`.
      *Done 3 Oct:* `ComplaintRequest` (all optional, one line, max 120/40/160 characters, no extra keys). A live API test
      checks the `cases` row and captured logs at DEBUG. A browser run against a local server found none of the values in
      the backend or frontend logs. An empty field prints a dotted line to fill in by hand.
- [x] **5.5 `POST /v1/cases/{id}/complaint`** streams the PDF (or a short-lived signed URL).
      Check: `curl -o c.pdf` → valid PDF; the UI download button works on the phone. Ports: new.
      *3 Oct:* returns `application/pdf` (attachment, `no-store`); nothing is stored. Returns 409 before analysis, for
      out-of-scope cases, and when there's no Writer facts section (also for analyses saved before CHANGES.md 22, which
      still load). The results page has a download card (`docs/screens/s5-complaint-card-ur.png`). Live runs on the local
      server (Gemini): TC-02 ur → 6,229.59, TC-03 en → 16,056.85, PDFs in `docs/arabic_review/`. Chromium at 375 px
      downloads the file. **Left open until the phone check** on the public URL after deploy.
      *4 Oct, phone check (iPhone, public URL):* the PDF is right (TC-02: 6,229.59, Western digits, RTL Arabic joined;
      `docs/screens/s5-phone-complaint-p1.jpg`, `-p2.jpg`), but the button **opened** it instead of saving it: iOS Safari
      ignores `<a download>` for a blob PDF. Fix (your choice): on phones the button prepares the PDF, then **"Save or
      share PDF"** opens the system share sheet (Save to Files, WhatsApp, Print), with an "Open PDF" fallback and an
      iPhone hint (`lib/share.ts`, `docs/screens/s5-complaint-share-ur.png`). Desktop still downloads directly.
      *Done 4 Oct:* on the iPhone, after PR #16, Download → **Save or share PDF** → saved to Files (your check).
- [ ] **5.6 Arabic reader review**.
      Check: a named reviewer signs off (tone + correctness), and notes go in `docs/arabic_review.md`. Ports: new.
      *3 Oct:* the review pack is ready (`docs/arabic_review.md`, with the TC-02 and TC-03 PDFs). Waiting for a reviewer.
      *4 Oct:* PDFs regenerated with Western digits (CHANGES.md 23). **Deferred (your call):** you'll do the sign-off later
      with an Arabic reader; Sprint 6 goes ahead meanwhile.

## Sprint 6 — Voice and languages (PRD Block 6)

- [x] **6.1 `POST /v1/transcribe`** (speech-to-text provider chosen here; Groq is unavailable, see 0.1; size and duration limits; audio is not stored).
      Check: `curl -F audio=@tests/fixtures/hi.webm` → `{text, detected_language:"hi"}`. Ports: new (F1 voice).
      *Done 4 Oct:* Whisper large-v3-turbo on Cloudflare Workers AI (`haqqi/speech.py`, `haqqi/api/transcribe.py`). The curl
      check returns the TC-01 sentence with `detected_language: "hi"`; with `language=ur` the same speech comes back in Urdu
      script. WebM/Opus (Chrome, Android) and MP4 (iPhone Safari) both transcribe. Limits: 3 MB (413), audio types only
      (415), empty (422), service down → 503 "please type". Audio and text are never stored or logged. The fixture is the
      TC-01 story in a synthetic voice (`tests/fixtures/README.md`).
- [x] **6.2 Mic recording in the browser** (MediaRecorder, iOS Safari fallback format).
      Check: record → transcript appears in the story box on Android Chrome and iOS Safari. Ports: new.
      *4 Oct:* `components/voice-input.tsx`: tap Speak → record (WebM/Opus, or MP4 on iPhone) → Stop or 2-minute limit →
      the text is added below what's already typed. Messages for a blocked microphone, no browser support, nothing heard,
      and service down. Chromium (Pixel 7 profile, fake mic playing the Hindi clip): the text appears in /hi (Devanagari)
      and /ur (Urdu script), with no console errors or sideways scroll.
      *Done 4 Oct:* on your iPhone (Safari, public URL) the recording was transcribed well and the case went through to
      the complaint. Android Chrome is covered only by the automated Pixel 7 run so far; try a real Android phone when you can.
- [ ] **6.3 Language matrix**: run TC-01 (hi), 02 (ur), 03 (en), 04 (ml), 05 (tl), 06 (bn), 08 (ne) and 23 (ar) through
      the UI; note output quality per language in `docs/language_check.md`.
      Check: the table is filled, and native/fluent reviewer notes are recorded where available. Ports: harness cases.
      *4 Oct:* all 8 run on the free Gemini models (`eval/language_check.py`, `docs/language_check.md`). Totals all match,
      every script's PDF font is embedded, no Writer failures, 12–49 s per case. Found for 6.4: TC-02 (Urdu) told the
      worker they are not entitled to gratuity ("under one year") while the claim shows 3,229.59 (the model miscounted
      2.3 years); TC-01 (Hindi) over-promises ("we will get your salary back"); TC-06 (Bengali) headline is vague.
      **Open:** native/fluent reader notes.
- [x] **6.4 Fix the worst language issues** (prompt tweaks, UI strings).
      Check: re-run the affected cases. Ports: new.
      *Done 4 Oct:* CHANGES.md 24–26 (**wording for your review**): the agents get the calculator's service length
      (SERVICE) and must not contradict calculated items; the Critic checks that; a code guard drops a contradicting
      not_covered note; the Writer must not promise results and the headline must name the problem. Re-run: TC-02 now
      says gratuity is due (6,229.59), TC-01 no longer promises, TC-06 headline names both issues
      (`docs/language_check.md`).
- [ ] **6.5 (P1) TTS playback** of the explanation. First to cut. **Skipped (your call, 4 Oct).**
      Check: play button reads the Hindi explanation. Ports: new (F9).

## Sprint 7 — Evaluation (PRD Block 7)

- [x] **7.1 Port the harness cases**: all 22 n8n cases → `eval/cases.jsonl` (story, form fields, expected outcome,
      issues, articles, hand-calculated claim, `max_total`, `expect_revise`, `expect_not_covered`).
      Check: `python -m eval.validate` → 22 valid rows. Ports: `Test Cases`.
      *Done 4 Oct:* `eval/cases.jsonl` (format in `eval/schema.py`). Each row has the story, form, confirm-form answers,
      expected route/referral, issues, key clauses (for hit@5), supporting articles (flag 24), and hand-worked claim
      lines and total (`eval/CASES.md`); TC-10/TC-14 carry injected amounts, TC-11 a seeded citation. `make eval-validate`.
- [x] **7.2 Add 28 cases** (to 50), weighted toward termination, gratuity and mixed issues, each with hand-worked claims.
      Check: validator → 50 rows; issue-type histogram printed. Ports: new.
      *Done 4 Oct:* N-01–N-28 in all 8 languages, with the edge cases: exactly 1 year, 364 days, exactly 5 × 365, the cap,
      part-time, flexible, unpaid absence, notice clamp, resigned short of notice, deductions over 50%, leave at the
      end of a job, above the 50,000 limit, injection, a second seeded citation, need-info, and free zone/ADGM. The
      validator shows 50 rows (40 ready, 6 out of scope, 4 need-info), with gratuity 23, unpaid wages 13, termination 11,
      notice 11. The app's calculator matches the independent hand arithmetic on all 40.
- [x] **7.3 `eval/run_eval.py`**: runs the pipeline per case and computes the 8 PRD metrics (outcome, issue detection,
      hit@5, citation validity, critic catch, calculator exact, injection resistance, p95 latency).
      Check: `make eval` prints the metrics table and writes `eval/results/<date>.json`. Ports: `Loop Over Items`, `Run Haqqi`, `Check Result`, `Summary`, `Is Test Run?`, `Return to Tests`, `When Executed by Another Workflow`.
      *Done 4 Oct:* in-process pipeline per case. Each case's result is saved as it finishes, so a run resumes, and
      `--rerun`/`--limit` let it be split across days or providers. K2 by default (your choice for eval);
      `--provider gemini` uses the free chain. Metric definitions are in `eval/metrics.py`; `eval/compare.py` gives a
      before/after on the same cases. First full K2 run: 16 of 50 cases were lost to a K2-only retry bug (HTTP 400,
      fixed). **Your call (4 Oct):** 20 cases today (TC-01 to TC-21), and the other 30 tomorrow on a Gemini + K2 mix.
- [x] **7.4 Offline eval subset for CI**: calculator exactness + retrieval hit@5 with no LLM.
      Check: `make eval-offline` finishes in < 2 min without `K2_API_KEY`; it exits non-zero if calculator < 100%. Ports: new.
      *Done 4 Oct:* `eval/offline.py`: calculator vs all 40 hand-worked cases (40/40) in about a second, no LLM, DB or key;
      CI runs it after the tests. Retrieval hit@5 runs too when a local BGE-M3 index is reachable (story as the query),
      otherwise it says "skipped".
- [x] **7.5 Fix the worst failures** (top 3 by metric gap).
      Check: before/after table in `eval/CHANGELOG.md`. Ports: new.
      *Done 4 Oct (20 cases, K2):*
      - Retrieval hit@5 went from 50% to 75%: issue words are added to the search query. The 3 remaining misses were
        unpaid wages, where CR 16 ranks above Art. 22. **Your call (4 Oct): CR 16(1) counts as a hit.** Re-scored on
        the same 20 cases, that is 60% before and **92%** after. One miss is left (TC-11).
      - No false notice breaches: CHANGES.md 27, approved. In TC-21 the false finding is gone.
      - Support labels widened by documented rules. Re-scored on the same labels, support is 98% before and 96% after.
      - The K2 retry fix: 0 cases lost.
      - Latency stays a K2 limit (p95 299 s); production runs on Gemini.
- [ ] **7.6 Record scores**.
      Check: the README metrics table matches the latest results file. Ports: `Log Results` (replaced).
      *4 Oct:* the README has the table for the 20-case K2 run, marked partial. It stays open until all 50 have run.

## Sprint 8 — Production polish (PRD Block 8)

- [ ] **8.1 Full CI**: ruff, mypy, eslint, tsc, pytest, calculator tests, `make eval-offline`, ingest smoke; on merge to
      `main`, build the image and deploy both services.
      Check: a PR shows all jobs green; merging triggers a deploy and `/healthz` shows the new commit SHA. Ports: new.
- [ ] **8.2 Langfuse tracing** of every K2 call (stage, latency, tokens) with PII redaction.
      Check: one run → a trace with 4–5 spans; searching the trace for the test phone number finds nothing. Ports: `Log Stats` (replaced).
- [x] **8.3 Log redaction**: a filter drops story text and masks phones, emails and Emirates ID/passport patterns.
      Check: `pytest tests/test_redaction.py`; grepping logs after TC-01 finds no story text. Ports: new.
      *Done 4 Oct:* `haqqi/logs.py`. Until now the app set up no logging of its own, so only warnings reached Render and
      nothing was filtered. The app now logs to stderr through `RedactingFilter`, which is also added to uvicorn's
      handlers. It masks phones and other 9+ digit numbers, emails, Emirates ID, passport-like ids and **case ids**
      (with no accounts, a case id is the only key to a case, so access logs show `/v1/cases/[case-id]`). It drops
      exception messages, which can quote the input, keeping the type and stack frames, and caps lines at 600
      characters. Our own log lines carry no content. A live API test runs TC-01 into a crash whose error quotes the
      story and finds neither the story nor the case id in the logs. Also: `make test-live` now uses its own
      `haqqi_test` database, because it had been overwriting the real local index.
- [x] **8.4 Rate limiting + input caps** (per IP; story, audio and form sizes).
      Check: 30 rapid requests → HTTP 429; oversized audio → 413. Ports: new.
      *Done 4 Oct:* `haqqi/api/limits.py`, an ASGI middleware inside CORS (so the browser can read a 429; the UI
      already shows its "busy" message). Per IP, in memory (one instance): new case 10 and analysis 10 per 10 minutes
      (they use the free Gemini quota, about 12–15 cases a day in all), complaint and voice 20 per 10 minutes, and any
      `/v1` call 120 a minute. `/healthz` is not limited. The IP is the last `X-Forwarded-For` entry (earlier ones can
      be faked). **To check after deploy:** if Render adds hops of its own, every user would share one limit. Bodies
      over 64 KB (3 MB + 64 KB for audio) get 413 before they are read; chunked bodies with no length get 411. The
      story, contract and complaint-field caps were already in place (3.4, 5.4, 6.1). Test: 30 rapid creates → 10
      reach the app, then 20 × 429 with Retry-After and CORS headers.
- [x] **8.5 Low-confidence route**: weak retrieval or all-low confidence → "I'm not sure" + MOHRE contacts.
      Check: TC-12 shows the not-covered/unsure path with contacts. Ports: `not_covered` handling in `Build Writer Prompt`.
      *Done 4 Oct (your choice: notice + keep the amounts):* code decides, with no prompt change.
      `Analysis.unsure` = in scope and no finding of medium or high confidence (no findings at all counts, like
      TC-12). It is always recomputed from the findings, so saved analyses get it too. The results page then:
      - leads with "Haqqi isn't sure about your case… call 80084, use the MOHRE app, or visit mohre.gov.ae" and a
        tap-to-call button (shared with the referral page);
      - titles the findings "Possible issues (low confidence)" and the amounts "if the law applies";
      - hides the complaint card. The server also refuses the PDF (409), so it isn't only hidden in the UI.

      "Weak retrieval" is not used as a signal: RRF ranks aren't calibrated scores, and the Law Pack always tops up
      the law. The new strings in the 7 non-English catalogs are drafts for review. Tests:
      - the rule table;
      - the PDF refusal;
      - a live API test (low finding → `unsure`, complaint 409);
      - the catalog 80084 check;
      - a browser run at iPhone width with the API mocked (`docs/screens/s8-unsure-en.png`, `-ur.png`), where a
        confident case is unchanged.
- [x] **8.6 7-day auto-delete** (flag 21): a scheduled purge job.
      Check: a test inserts a case dated 8 days ago → purge removes it; the job is visible in the host scheduler. Ports: new.
      *4 Oct:* Render's free plan has no cron jobs and the backend sleeps, so the schedule lives in the database:
      migration `0002` creates an hourly **pg_cron** job on Supabase (`DELETE FROM cases WHERE expires_at <= now()`); where
      pg_cron isn't available (the local image) it is a no-op, and `python -m haqqi.purge` does it by hand. The API
      already refused expired cases. The live test (a case from 8 days ago is deleted, a new one kept) passes.
      *Done 4 Oct:* migrated on Supabase (`0002 (head)`). `cron.job` lists `haqqi-purge-expired-cases`, hourly
      at :17, active (your check).
- [x] **8.7 Disclaimer everywhere** (results, referral, PDF footer).
      Check: every eval response includes "80084" (ported `disclaimer` check). Ports: `DISCLAIMER`/`DISCLAIMER_AR` constants.
      *Done 4 Oct:* mostly in place since S4/S5; this adds the missing checks. Screens: the `[lang]` layout shows the
      disclaimer on every page (English, the worker's language and Arabic, each with 80084), and a catalog test keeps
      80084 in every language's disclaimer and referral line. The results page and the story screen say the text is
      processed by Google Gemini (flag 26). Referral texts from routing include 80084 (API test). PDF: new tests check
      the footer ("legal information, not legal advice; MOHRE decides … 80084") in both columns for all 8 languages,
      and in the PDF text. The API's JSON has no disclaimer field: the UI adds it, so the check is on what the worker
      sees.
- [ ] **8.8 Sentry** for the frontend and backend.
      Check: a test exception shows up in Sentry. Ports: new.
- [ ] **8.9 README**: problem, architecture diagram, eval table, demo GIF, setup, and the n8n "v0" story.
      Check: the README renders on GitHub with the image and table. Ports: `Setup` note.
- [ ] **8.10 90-second demo video**.
      Check: the file or link is in the README. Ports: new.

## Definition of done (from PRD)
- [ ] Public URL works on a phone end to end in ≥ 4 languages
- [ ] Every violation shows an article citation; every amount shows its formula
- [ ] Arabic PDF renders correctly and was checked by an Arabic reader
- [ ] Eval scores in README; calculator tests at 100%
- [ ] CI green on `main`; README has architecture diagram and demo GIF

## n8n node coverage (31 functional nodes + the Setup sticky note)
Setup→2.2/8.9 · Haqqi Form→4.2–4.4 · When Executed by Another Workflow→7.3 · Normalize Input→3.4 ·
Build Intake Prompt/K2 Intake/Parse Intake→3.5–3.7 · Route Case→3.3 · Law Pack→2.1/2.7 · Calculator→3.2 ·
Build/K2/Parse Analyst→3.9 · Build/K2/Parse Critic→3.9 · Critic Passed?→3.9 · Build/K2/Parse Revision→3.9 ·
Build/K2/Parse Writer→3.10/5.2 · Assemble Case Pack→3.11/4.6 · Out-of-Scope Reply→4.7 · Need-Info Reply→4.4 ·
Is Test Run?/Return to Tests→7.3 · Log Stats→8.2 · Has Email?/Email Case Pack→dropped (flag 11) · Show Result→4.8
