# Haqqi — Product Requirements Document

Sep 29, 2026 · @raqt

## Overview

Haqqi (حقي, "my right") helps blue-collar workers in the UAE understand whether their employer broke the labour law, what they are owed, and how to file a formal complaint in Arabic, all in their own language. It was built in one day for the n8n Dubai Hackathon, "Automate with K2 Horizon" (25 Sep 2026), and placed in the top 4 of 400+ participants. This PRD scopes the production rebuild over Sep 29–30.

**What already exists (hackathon build).** A 31-node n8n workflow on K2 Horizon (`IFM/K2-Horizon-375B-A23B`) with four agents: Intake → Analyst → Critic (one bounded revision) → Writer. A Law Pack of 10 topics with official English text from Federal Decree-Law No. 33 of 2021, a deterministic calculator, out-of-scope and need-info routes, and a 12-case test harness covering prompt injection and a seeded bad citation.

**What the rebuild changes.** The logic and prompts carry over; the platform does not. n8n becomes a typed Python service with a real web app, retrieval over the full law instead of a hand-picked pack, voice input, a proper Arabic PDF, a larger measured evaluation, and CI/CD. The agent design is the strongest part of the hackathon build and stays.

**Goals for this build**

- A deployed web app a worker can use end to end: tell their story, get a verdict, see their claim amount, download an Arabic complaint.
- Every legal statement cites a specific article; every money figure comes from a deterministic calculator, never the LLM.
- Measured quality: a published evaluation of retrieval and answer accuracy.
- Production practices: typed API, tests, Docker, CI/CD, tracing, basic security.

**Non-goals for this build**

- WhatsApp channel (designed for, built later).
- Filing directly with MOHRE (the app prepares the complaint; the worker submits it).
- DIFC, ADGM and domestic-worker cases (separate legal regimes; detected and redirected, not analysed).
- Scale beyond demo traffic, user accounts, or payments.

## Problem statement

The UAE resolves almost every labour dispute that reaches MOHRE, but reaching MOHRE with a clear, correct claim is the hard part for low-wage migrant workers. Haqqi targets that first step.

**The system works once a case is filed.** MOHRE recorded about 188,000 labour disputes in H1 2026 (roughly 1,000 per day), settling 185,793 of them (98.6%) and referring only 2,481 (1.4%) to court ([WAM, Aug 2026](https://www.wam.ae/en/article/c1kxr4e-mohre-resolves-986-labour-disputes-amicably-2026)). Since 1 January 2024, MOHRE itself can decide claims up to AED 50,000 ([MOHRE](https://mohre.gov.ae/en/media-center/news/9/3/2026/mohre-successfully-settles-98-percent-of-labour-disputes-in-2025)).

**The gap is before filing.** MOHRE handled about 9.43 million labour consultation and complaint contacts in 2025, roughly 25,800 a day ([MOHRE](https://mohre.gov.ae/en/media-center/news/9/3/2026/mohre-successfully-settles-98-percent-of-labour-disputes-in-2025)), many of them basic "what are my rights" questions. Workers who are underpaid, unpaid, or denied gratuity typically face three barriers:

- **Language.** The law and formal complaints are in Arabic and English; many workers speak Hindi, Urdu, Malayalam, Bengali, Nepali or Tagalog.
- **Legal knowledge.** They don't know which rights apply (mainland vs free zone, contract terms), which articles were broken, or what they are owed.
- **Power imbalance.** Employers can exploit that gap, and a vague or wrong claim is easier to dismiss.

**Why now.** Volume is high, the resolution machinery is fast, and LLMs can finally explain law in a worker's own language. What's missing is a trustworthy bridge: cited, calculated, and ready to file.

**Pitch line:** "MOHRE settles 98.6% of disputes. Haqqi helps the workers who never get as far as filing one."

Open question: find a source for how many workers never file (e.g. an NGO or ILO report). It would make the gap concrete in interviews.

## Users and journey

The primary user is a worker on a phone with limited literacy; every screen must work by voice and in their language.

| Persona | Situation | Language | Needs from Haqqi |
| --- | --- | --- | --- |
| Ramesh, construction helper | Salary unpaid for 3 months, still employed | Hindi | Plain explanation of rights, amount owed, a complaint draft |
| Ayesha, retail cashier | Terminated the same day with no notice pay | Urdu | Whether the termination was lawful and what notice pay is due |
| Joel, hotel staff | Resigned after 6 years; gratuity offer looks low | English, Tagalog | Step-by-step gratuity check against the law |
| Community volunteer | Helps many workers each week | English, Arabic | Fast, consistent case summaries and printable complaints |

Persona names and cases are illustrative, not real people.

**Core journey (web, v1)**

1. **Choose language** on the landing screen (flags plus the language's own script).
2. **Tell the story** by voice or text, in any supported language.
3. **Answer a short structured form:** emirate, mainland or free zone, contract type, start date, basic and total monthly wage, last day worked, and what happened. Fields the story already answered are pre-filled for confirmation.
4. **See the verdict:** which rights were likely violated, each tied to a cited article, in plain language.
5. **See the claim:** an itemised amount (unpaid wages, gratuity, leave, notice) from the calculator, with the formula shown.
6. **Get next steps:** where and how to file, deadlines, documents to gather.
7. **Download the complaint:** a formal Arabic complaint PDF plus a translation in their language, ready to submit to MOHRE.

If the case falls outside scope (DIFC, ADGM, domestic worker) or confidence is low, the flow stops at step 4 with a referral instead of a verdict.

## Functional requirements

Ten capabilities, split by priority: P0 ships by end of Sep 30; P1 only if time allows.

| ID | Capability | Requirement | Carried from hackathon? | Priority |
| --- | --- | --- | --- | --- |
| F1 | Intake agent | Voice (Whisper) or text in 7 languages; K2 extracts structured facts; user confirms or edits them in a form | Yes (add voice and confirm step) | P0 |
| F2 | Case routing | Out of scope (free zone, DIFC/ADGM, domestic) → redirect; missing salary or start date → ask for it; otherwise analyse | Yes | P0 |
| F3 | Law retrieval | Hybrid retrieval over the full law and executive regulations, merged with the issue-type Law Pack; code rejects any article id not retrieved | Upgrade | P0 |
| F4 | Claim calculator | Deterministic Python, no LLM: unpaid wages, deductions, notice pay, gratuity, each with its formula | Port from JS | P0 |
| F5 | Analyst → Critic → Revise | Analyst maps facts to cited articles; Critic checks every citation and amount; one bounded revision on failure | Yes | P0 |
| F6 | Writer agent | Plain explanation in the worker's language plus a formal Arabic letter from a fixed template | Yes | P0 |
| F7 | Complaint PDF | Arabic letter rendered right to left with a side-by-side translation; downloadable | New | P0 |
| F8 | Progress streaming | Show each agent's stage live while the worker waits | New | P0 |
| F9 | Text-to-speech | Read the explanation aloud | New | P1 |
| F10 | WhatsApp channel | Same flow over the WhatsApp Business API | Planned | P1 (design only) |

**Supported languages (v1):** English, Hindi, Urdu, Malayalam, Bengali, Tagalog, Nepali (the hackathon set). Arabic for the complaint output. Tamil next.

**Calculator rules (F4).** Already encoded in the hackathon calculator with article references (Art. 51 gratuity, Art. 53 payment within 14 days); cross-checked against the [official UAE government portal](https://beta.government.ae/en/information-and-services/jobs/end-of-service-benefits-for-employees-in-the-private-sector).

| Item | Rule | Base |
| --- | --- | --- |
| Gratuity eligibility | At least 1 year of continuous service; unpaid absence days excluded | Service days |
| Gratuity, years 1–5 | 21 days' wage per year | Basic wage ÷ 30 |
| Gratuity, after year 5 | 30 days' wage per year | Basic wage ÷ 30 |
| Gratuity cap | Total never exceeds 2 years' wage | Basic wage |
| Payment deadline | All end-of-service dues within 14 days of the contract's end | Termination date |
| Unpaid wages | Months unpaid × total monthly wage | Total wage |
| Leave encashment | Unused annual leave days × daily wage | Basic wage ÷ 30 |
| Notice pay | Notice period owed if terminated without notice | Total wage |

Every rule is unit-tested with hand-worked cases, including edge cases: exactly 1 year, exactly 5 years, cap hit, part-time contract.

## System architecture

The hackathon's agent pipeline stays; what changes is everything around it: a real web app, an API, retrieval over the full law, and a PDF at the end.

&#91;embedded content: Haqqi request flow · 4 K2 agents, 2 decisions\]

Only the tinted steps call K2 Horizon. Routing, retrieval, arithmetic and citation checks are code, so no amount or article reaches the worker without being checked. Postgres holds the law index; Langfuse traces every K2 call. Tech choices are listed under Deployment and operations.

## Knowledge base

Start from the hackathon Law Pack, which already holds official English text for 10 topics (wages, deductions, termination, notice, gratuity, leave, overtime, documents, time limit, procedure). The rebuild adds the Arabic text and the rest of the law around it, so issues the Intake agent doesn't tag can still be found.

**Sources (v1)**

| Source | Language | Use |
| --- | --- | --- |
| Federal Decree-Law No. 33 of 2021 on the Regulation of Labour Relations | English + Arabic | Core rights and obligations |
| Cabinet Resolution No. 1 of 2022 (Executive Regulations) | English + Arabic | Procedures, part-time gratuity, leave details |
| Federal Decree-Law No. 20 of 2023 (amendment) | English + Arabic | MOHRE's power to decide claims up to AED 50,000 |
| MOHRE service pages and FAQs | English | How to file, required documents, contact channels |

Download the official English and Arabic PDFs from the UAE legislation portal and MOHRE; record URL and retrieval date for each.

**Chunking and metadata**

- One chunk per article (split long articles by numbered clause), never fixed-size windows.
- Store English and Arabic text of each article side by side, linked by article number.
- Metadata per chunk: `law_id`, `article_no`, `clause_no`, `title`, `topic_tags` (wages, gratuity, leave, termination, notice, overtime, complaints), `source_url`, `effective_date`.

**Indexing**

- Dense vectors with a multilingual embedding model (e.g. BGE-M3 or multilingual-e5), stored in Postgres with pgvector.
- Keyword index with Postgres full-text search (BM25-style) on the English and Arabic text.
- Merge the two ranked lists with reciprocal rank fusion, then keep the top 5–8 articles.

**Ingestion is a script, not a notebook:** `python -m haqqi.ingest` rebuilds the index from the raw PDFs and is run in CI to check it still works.

## API and data models

A small REST API; each step of the journey is its own endpoint so it can be tested and traced separately.

| Method | Endpoint | Does | Returns |
| --- | --- | --- | --- |
| POST | `/v1/transcribe` | Audio upload → Whisper | `{text, detected_language}` |
| POST | `/v1/cases` | Story + language → field extraction | `Case` with extracted fields marked for confirmation |
| PATCH | `/v1/cases/{id}` | User confirms or edits fields | Updated `Case` |
| POST | `/v1/cases/{id}/analyze` | Jurisdiction check, retrieval, violation analysis, calculator (streamed) | `Analysis` |
| POST | `/v1/cases/{id}/complaint` | Arabic complaint + translation | PDF download URL |
| GET | `/healthz` | Liveness and dependency checks | `{status}` |

**Core models (Pydantic)**

```python
class CaseFacts(BaseModel):
    language: Literal["en", "hi", "ur", "ml", "bn", "tl", "ne"]
    emirate: Emirate
    zone: Literal["mainland", "free_zone", "difc", "adgm"]
    worker_type: Literal["private_sector", "domestic"]
    contract_type: Literal["full_time", "part_time", "temporary", "flexible"]
    start_date: date
    end_date: date | None
    basic_wage_aed: Decimal
    total_wage_aed: Decimal
    months_unpaid: int = 0
    unused_leave_days: int = 0
    termination: Literal["employer", "resigned", "still_employed"]
    notice_given: bool | None
    story: str

class Violation(BaseModel):
    issue: str
    article: Citation          # law_id, article_no, clause_no, quote
    confidence: Literal["high", "medium", "low"]

class ClaimLine(BaseModel):
    item: str                  # e.g. "Gratuity"
    amount_aed: Decimal
    formula: str               # e.g. "21 × (2,000 ÷ 30) × 3 years"
    article: Citation

class Analysis(BaseModel):
    in_scope: bool
    referral: str | None
    violations: list[Violation]
    claim: list[ClaimLine]
    total_aed: Decimal
    explanation: str           # in the user's language
    next_steps: list[str]
```

The LLM returns structured output validated against these models; money fields are only ever written by the calculator.

## Evaluation, safety and privacy

The evaluation table is the single strongest line on the resume; build the test set before tuning anything.

**Evaluation set:** 50 cases in `eval/cases.jsonl`. Port the 12 hackathon cases first (TC-01 to TC-12: seven languages, both out-of-scope routes, missing info, prompt injection, seeded bad citation, not covered), then add 38 more, weighted toward termination, gratuity and mixed-issue cases. Each case holds the story, the expected outcome, the expected articles and the hand-calculated claim.

| Metric | What it checks | Target |
| --- | --- | --- |
| Outcome accuracy | Correct route: case pack, out of scope, or need info | ≥ 95% |
| Issue detection | All expected issue types found | ≥ 85% |
| Retrieval hit@5 | Correct article in the top 5 results | ≥ 90% |
| Citation validity | Every finding cites an article that supports it (code check + Critic) | 100% cited, ≥ 90% supported |
| Critic catch rate | Seeded bad citations flagged and fixed by the revision | ≥ 90% |
| Calculator correctness | Exact match with hand calculations | 100% |
| Injection resistance | Injected amounts never appear in the claim | 100% |
| Latency | Full case pack, p95, with progress streamed | < 90 s |

Run it with `make eval`; CI fails if calculator correctness drops below 100%. Publish the latest scores in the README.

**Safety and guardrails**

- Clear disclaimer on every result: legal information, not legal advice; MOHRE decides.
- Low retrieval confidence → "I'm not sure" plus MOHRE contact options, never a guess.
- The LLM never computes money and never invents article numbers; citations are checked against the index before display.
- Prompt-injection defence: the story is treated as data inside delimiters; outputs are schema-validated.
- Rate limiting per IP and maximum input length.

**Privacy**

- Worker data is highly sensitive (employer name, wages, possibly passport details). Store only what the complaint needs.
- Cases auto-delete after 7 days; no training on user data.
- Redact phone numbers and ID numbers from logs and traces.
- No accounts in v1: a case is reached only through its unguessable ID.

## Deployment and operations

Two deployables, one database, one pipeline: simple enough to finish in two days, real enough to discuss in interviews.

| Area | Choice | Why |
| --- | --- | --- |
| Frontend | Next.js (App Router), Tailwind, shadcn/ui on Vercel | Free, instant previews per pull request |
| Backend | FastAPI in Docker on Render, Railway or Fly.io | Container deploy from GitHub |
| Database | Postgres + pgvector on Supabase or Neon | One store for cases, vectors and full-text search |
| LLM | K2 (primary), second provider as fallback | Keeps the IFM story; demo never dies |
| Speech | Whisper API | Multilingual transcription |
| PDF | WeasyPrint with Noto Naskh Arabic font | Correct Arabic letter joining and right-to-left layout |
| Tracing | Langfuse | Per-request trace, cost and latency |
| Errors | Sentry (free tier) | Frontend and backend exceptions |

**CI/CD (GitHub Actions):** on every pull request run lint (ruff, eslint), type checks (mypy, tsc), unit tests (pytest) and the calculator tests; on merge to `main` build the image and deploy both services.

**Repo layout**

```
haqqi/
  frontend/        Next.js app
  backend/
    haqqi/api/     FastAPI routes
    haqqi/core/    calculator, jurisdiction rules
    haqqi/rag/     ingest, retrieval, prompts
    haqqi/pdf/     complaint templates
    tests/
  eval/            cases.jsonl, run_eval.py
  docker-compose.yml
  .github/workflows/
  README.md        problem, demo GIF, architecture, eval scores
```

**Secrets** live in the host's environment settings, never in the repo; `.env.example` lists them.

## Two-day build plan

Eight focused blocks of about 2 hours each, four per day, so they fit around your other commitments. Day 1 ends with a deployed end-to-end flow; Day 2 makes it trustworthy.

**Day 1: Sep 29 — working end to end**

- [ ] **Block 1 — Skeleton.** Repo, Next.js + FastAPI scaffold, Docker Compose, deploy "hello world" to Vercel and the backend host. Give Claude Code this PRD first.
- [ ] **Block 2 — Knowledge base.** Load the hackathon Law Pack, download the full law PDFs (English and Arabic), write the ingest script, chunk by article, load pgvector and full-text index. Check 10 queries by eye.
- [ ] **Block 3 — Core logic.** Port the n8n Code nodes to Python: calculator (unit-tested against TC-01 and TC-03), routing, and the four agents reusing the hackathon prompts, with Pydantic validation replacing the JavaScript parsers.
- [ ] **Block 4 — UI flow.** Language picker, story input, confirm-fields form, results page. Deploy; run one full case on your phone.

**Day 2: Sep 30 — trustworthy and presentable**

- [ ] **Block 5 — Arabic complaint.** Template, WeasyPrint with Noto Naskh Arabic, translation alongside. Test the PDF renders correctly first thing.
- [ ] **Block 6 — Voice and languages.** Whisper input, test each of the 7 languages with a native or fluent speaker if possible.
- [ ] **Block 7 — Evaluation.** Write the 50 cases, run `make eval`, fix the worst failures, record scores.
- [ ] **Block 8 — Production polish.** CI pipeline, Langfuse tracing, rate limits, disclaimer, README with architecture diagram, eval table and demo GIF; record a 90-second demo video.

**If time runs short, cut in this order:** text-to-speech playback → Bengali and Tagalog (keep 4 languages) → Langfuse → reduce eval set to 30 cases. Never cut: calculator tests, citations, the Arabic PDF, deployment, README.

**Definition of done**

- [ ] Public URL works on a phone, end to end, in at least 4 languages
- [ ] Every violation shows an article citation; every amount shows its formula
- [ ] Arabic PDF renders correctly and was checked by an Arabic reader
- [ ] Eval scores in the README; calculator tests at 100%
- [ ] CI green on `main`; README has architecture diagram and demo GIF

## Validation, resume and open questions

Five short conversations before Oct 7 turn "I built an app" into "I built what workers told me they need."

**Who to talk to (aim for 5, 15 minutes each)**

- 2–3 workers you can reach through friends, building staff, drivers or delivery riders.
- 1 community helper: a consulate welfare desk, NGO volunteer or labour-camp organiser.
- 1 person who reads Arabic well, to check the complaint's tone and correctness.

**What to ask**

1. When something went wrong at work, what did you do first? Who did you ask?
2. Did you know you could complain to MOHRE? What stopped you, or what was hardest?
3. (Show the app) Would you trust this answer? What would make you trust it more?
4. Would you use this on WhatsApp or a website? Voice or typing?

Ask permission before quoting anyone, and keep their names out of the README.

**Resume bullets (fill real numbers after Block 7)**

- Built Haqqi, a multilingual legal-aid assistant for UAE migrant workers (Next.js, FastAPI, Postgres/pgvector, K2), top 4 of 400+ at the n8n Dubai Hackathon (K2 Horizon).
- Hybrid retrieval over UAE labour law with article-level citations; \_\_% hit@5 and \_\_ faithfulness on a 50-case evaluation set in 7 languages.
- Deterministic claim calculator (gratuity, wages, leave, notice) with 100% test accuracy; Arabic complaint PDFs; Whisper voice input; CI/CD, Docker, tracing.

**Open questions**

- Does your K2 Horizon API key (api.ifm.ai) still work after the hackathon, and at what rate limits? Confirm before Block 3; four to five sequential calls per case add up.
- Can you keep the hackathon n8n workflow public as "v0" in the repo? Showing the n8n-to-code evolution is a strong interview story.
- Does MOHRE accept complaints filed on behalf of a worker by a helper? Affects the community-helper persona.
- Which free zones follow federal labour law for the claim calculation? Treat as "confirm with the free zone authority" until checked.
