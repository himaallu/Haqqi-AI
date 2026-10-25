# Haqqi Chat — Brainstorm and Implementation Plan (pilot)

Status: **draft for your review**, 24 Oct 2026. Nothing here is built yet.
Builds on docs/PRD.md and docs/IMPLEMENTATION_PLAN.md (Sprints 1–8). Rules: CLAUDE.md.
Same conventions: one sprint at a time, **Check** = how we verify it, flags are approved before they are built.

## 1. The idea in one paragraph

Today Haqqi is a straight line: tell your story → confirm a form → get a verdict → download a complaint. It works
well for a worker who already knows something is wrong. But many workers arrive with something smaller:
*"Can my company keep my passport?"*, *"What does this line in my contract mean?"*, *"Is 6 months probation
normal?"*. The chat turns Haqqi into **one conversation with three doors**:

| Door | The worker says | Haqqi does | Ends with |
| --- | --- | --- | --- |
| **Ask** | a question about their rights | a short answer in their language, with the article it comes from | the answer, plus "ask another" or "check my situation" |
| **Contract** | "explain my contract" (photo or pasted text) | a plain-language summary of each key term, and red flags checked against the law | the summary card; its wage, dates and notice can pre-fill a case |
| **Case** | "something went wrong" (or a question that turns out to be one) | asks only for the missing facts, one at a time, then runs the **existing** pipeline | verdict, claim, next steps and the Arabic complaint, as cards in the chat |

The worker never has to pick a door correctly. They can start anywhere, and Haqqi moves between doors when
the conversation calls for it, but **it always asks before starting a case** ("It sounds like your salary is
late. Do you want me to check what you are owed?").

**What doesn't change:** the Analyst → Critic → Writer pipeline, the calculator, citation enforcement, routing,
the PDF and the 50-case eval. The chat is a new front door and a new, lighter "Guide" agent for questions. The case
door feeds the same `CaseFacts` into the same `analyze_case`, so every number and citation stays as trustworthy as now.

## 2. Designing for the user we have

Who: a migrant worker, on a cheap Android phone or an older iPhone, on mobile data, often tired, sometimes with
limited reading. Some arrive through a community volunteer. The design rules follow from that:

1. **Voice first, text always.** The mic is the biggest button on the screen. Tap to talk, tap to stop (hold-to-talk
   is hard for some users and breaks on iOS). The transcript shows in the message bubble so the worker sees what
   was understood and can fix it. Every Haqqi message has a ▶ Listen button (F9, revived for the chat).
2. **One question at a time.** No forms by default. When Haqqi needs a fact, it asks for it in one short sentence with
   **tap answers** (chips): emirate → 7 chips; "Are you still working there?" → Yes / No, I left / They fired me.
   Dates are "month + year" chips with an "exact day" option, because many workers don't remember the day.
3. **Short messages.** Answers are 2–4 short sentences, then "Tell me more" if the worker wants detail. No legal jargon
   in the main text; the article chip carries the legal detail.
4. **Show, don't just tell.** Money, facts and verdicts are **cards** (not paragraphs): a facts card with ✎ edit,
   a claim card with each line and its formula, a verdict card with article chips.
5. **Trust signals in place.** Every legal statement has a tappable article chip (`Art. 51`) that opens the law text
   (English + Arabic). A small "Legal information, not legal advice · MOHRE 80084" line sits above the composer,
   and a ☎ 80084 button is always in the top bar.
6. **Never a dead end.** Every reply ends with something to tap: a next question, "check my situation",
   "explain my contract", or "call MOHRE".
7. **Nothing to sign up for, easy to come back.** No account. The conversation id lives in the URL and in the phone's
   storage, so reopening Haqqi shows "Continue your conversation?" A **Delete my chat** button wipes it at once.
8. **Light and fast on bad data.** No chat library, no heavy assets, small JSON per turn, a typing indicator while the
   model works (2–6 s on Gemini Flash). Works on a 375 px screen with large tap targets (≥ 44 px), RTL for Urdu and Arabic.
9. **Shareable.** "Share on WhatsApp" for an answer, a contract summary or the case summary (text only, no personal data),
   because workers ask friends and volunteers there.
10. **Safety first, silently.** If a message mentions danger (violence, no food or water, locked in, passport taken
    and can't leave), Haqqi shows an emergency card first (police 999 and the verified hotlines, flag 7), then continues.

### Screen sketch (375 px)

```
┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│ Haqqi حقّي        🇮🇳 हिंदी   ☎ │      │ Haqqi حقّي        🇮🇳 हिंदी   ☎ │
├─────────────────────────────────┤      ├─────────────────────────────────┤
│  नमस्ते! मैं हक़्क़ी हूँ। ▶        │      │ [you] कंपनी ने 3 महीने से तनख़्वाह │
│  UAE में आपके काम के अधिकारों में  │      │       नहीं दी।                  │
│  मदद करता हूँ।                    │      │ [Haqqi] यह क़ानून के ख़िलाफ़ है।  │
│                                 │      │  वेतन हर महीने देना होता है।     │
│ ┌─────────────────────────────┐ │      │  (Art. 22)  ▶                    │
│ │ ❓ मेरा एक सवाल है           │ │      │ ┌ क्या मैं आपका केस देखूँ? ─────┐ │
│ ├─────────────────────────────┤ │      │ │ आपको कितना पैसा मिलना चाहिए,   │ │
│ │ 📄 मेरा कॉन्ट्रैक्ट समझाओ     │ │      │ │ यह हिसाब लगा सकता हूँ।         │ │
│ ├─────────────────────────────┤ │      │ │ [ हाँ, देखो ]  [ बाद में ]     │ │
│ │ ⚠️ काम पर कुछ ग़लत हुआ        │ │      │ └───────────────────────────────┘ │
│ └─────────────────────────────┘ │      │ [Haqqi] आप किस अमीरात में काम    │
│ लोग पूछते हैं:                   │      │ करते हैं?                         │
│ (पासपोर्ट रखना?) (ओवरटाइम?)     │      │ (Dubai)(Abu Dhabi)(Sharjah)(…)  │
├─────────────────────────────────┤      ├─────────────────────────────────┤
│ Legal info, not advice · 80084  │      │ Legal info, not advice · 80084  │
│ [📷] [ लिखें…            ] [🎤] │      │ [📷] [ लिखें…            ] [🎤] │
└─────────────────────────────────┘      └─────────────────────────────────┘
       empty state                              case door, slot-filling
```

## 3. How it works (architecture)

```
             ┌──────────── chat turn (POST /v1/chats/{id}/messages, SSE) ─────────────┐
 worker ───▶ │ safety check (code) → Guide agent (1 LLM call, JSON) → code checks     │ ───▶ cards
 text/voice/ │   intent: ask | contract | case | smalltalk | off_topic               │
 chip/photo  │   ask      → retrieve(question) → answer with cited chunk ids          │
             │   contract → OCR → redact → contract reader → summary + red flags      │
             │   case     → facts_update → route_case() → next question from a bank   │
             └───────────────────────────────┬─────────────────────────────────────────┘
                                              │ worker taps "Check my case" on the facts card
                                              ▼
                         existing: Intake (over the chat transcript) → CaseFacts → analyze_case()
                         → Analyst → Critic → (revise) → Writer → calculator → Analysis → PDF
```

Key choices:

- **One Guide call per turn, structured JSON** (CLAUDE.md: every reply is a Pydantic model). `GuideReply` =
  `{intent, reply, cited_chunk_ids, facts_update: ExtractedFacts-partial, offer_case: bool, safety: bool}`.
  The reply text is in the worker's language. We don't stream tokens: a typing indicator covers 2–6 s, and
  structured output can't be validated half-way. Stage events (`thinking`, `searching_law`, `reading_contract`) stream as now.
- **Code picks the next question, not the model.** After each case-door turn, code merges `facts_update`, runs the
  existing `route_case()` + `MISSING_FIELDS`, and picks the next missing field from a fixed **question bank** in the
  i18n catalogs, with its chips. A chip tap fills the field directly with **no LLM call** (saves quota, no errors,
  already translated). Only free-text answers go through the Guide.
- **The proven Intake still runs once at launch**, over the whole worker side of the chat, so the facts card comes
  from the same tested extractor as today; Guide `facts_update` values only pre-fill it, and chip answers win.
  The facts card is the confirm step (PATCH); "✎ Edit details" opens today's `ConfirmForm` as a bottom sheet.
- **Q&A answers obey the same trust rules.** Retrieval reuses `retrieve()` with the question (plus the Law Pack topic if
  the Guide tags one). `enforce_citations` drops any article not retrieved; an answer with no surviving citation becomes
  "I'm not sure, here is how to ask MOHRE". **No amounts from the LLM:** a reply with an AED figure is rejected (one retry),
  as the Writer does now. "How much gratuity would I get?" is answered by the calculator through `[[AMOUNT]]` tokens
  (flag 6), or by offering to check the case.
- **Results become chat cards.** `Results` is split into `VerdictCard`, `ClaimCard`, `NextStepsCard` and
  `ComplaintCard`, rendered inside the chat. After the results, follow-up questions ("why is my gratuity this much?")
  go to the Guide with the `Analysis` (findings, formulas, citations) as context: it explains, never recalculates.
- **Storage.** A new `chats` table: `id uuid, language, messages jsonb, draft_facts jsonb, case_id → cases, expires_at`
  (7 days, same pg_cron purge). Messages are stored only so the conversation can resume; never logged, never in traces.
  `/[lang]/case/[id]` keeps working (deep links, eval, volunteers who like the form).

### Contract door in detail

1. **Input:** 📷 take photos (up to 4 pages) or paste text. Before upload: "Cover your passport number and Emirates ID,
   or we will hide them for you."
2. **Text extraction** (flag 2 picks the provider): image → text. The image is never stored.
3. **Redaction in code** before any LLM sees it: passport, Emirates ID, labour card, phone and email patterns
   (reuse `haqqi/logs.py`'s patterns), and the worker's name if the Guide marked it.
4. **Contract reader** (new prompt, structured): `{job_title, employer_type, start_date, basic_wage_aed, total_wage_aed,
   weekly_hours, probation_months, notice_days, annual_leave_days, contract_type, free_zone_name, clauses: [{topic,
   plain_explanation, quote}], red_flags: [{issue, cited_chunk_ids}]}`.
5. **Red flags are checked by code where possible**, not left to the model: a short rule list (notice outside 30–90 days,
   probation over the legal maximum, weekly hours over the maximum, basic > total, no leave, fees charged to the worker,
   documents kept by the employer). Each rule cites its article id from `data/law`, verified by a test, so the model
   explains the red flag but doesn't decide whether it exists.
6. **Output:** a contract card ("Your contract in simple words": wage, hours, leave, notice, probation, each with a ✓ or ⚠)
   and "Use these details to check my case" (pre-fills `draft_facts`).
7. MOHRE standard contracts are bilingual and longer than today's 4,000-character `contract_text` cap: the contract
   path gets its own cap (about 20,000 characters, flag 9).

## 4. Decisions for you (flags)

**BLOCKER** = decide before the sprint that needs it; **RISK** = plan around it.

1. **BLOCKER (C1): LLM quota for a pilot.** Free Gemini is 20 requests per model per day (flag 18). A chat adds about
   5–10 calls per conversation on top of the 4–6 for a case, so free tiers serve maybe **5–8 conversations a day**, then K2
   (slow, 5–77 s per call, poor for chat). Options: (a) enable Gemini billing for the pilot (Flash costs cents per
   conversation, and the paid tier doesn't use data for training, which also fixes flag 26), (b) K2 for Guide turns,
   Gemini for the pipeline, (c) stay free and cap pilot traffic. **Recommendation: (a)**, with a hard monthly budget cap.
2. **BLOCKER (C4): who reads contract photos.** Contracts carry names, passport and labour card numbers.
   (a) Gemini vision (paid tier, flag 1), best quality and Arabic/English mixed text; (b) Cloudflare Workers AI vision
   model, same account as Whisper and BGE-M3, quality to be measured; (c) on-phone OCR (tesseract.js), private but a
   ~10 MB download and weak on photos. **Recommendation: (a) if flag 1 = paid, else measure (b)**; paste-text always works.
3. **BLOCKER (C2): chat replaces the form?** **Recommendation:** chat is the home screen; the form becomes "✎ Edit
   details" on the facts card. The old `/case/[id]` page stays for links and volunteers.
4. **BLOCKER (C5): text-to-speech provider.** Browser `speechSynthesis` is free and offline, but voices for Urdu,
   Malayalam, Nepali and Bengali are often missing on Android. Cloudflare's TTS models cover few of our languages.
   Google Cloud TTS covers all 7 but is paid. **Recommendation:** browser voices first, show ▶ only when the phone has a
   voice for the language, measure coverage on real phones in the pilot, then decide on a paid provider.
5. **DECISION (C1): question scope.** Labour rights only, or also visas, residency and bans (ICP / GDRFA territory)?
   **Recommendation:** labour law only (what our index covers); for visa questions, a polite redirect to the right authority.
6. **DECISION (C1): amounts in Q&A.** May Ask answers show a calculator figure ("21 days per year: with your 2,000
   basic and 3 years that is 4,200.00")? **Recommendation:** yes, calculator-only via tokens, and only from numbers the
   worker gave in the chat, labelled "estimate, confirm with your case check".
7. **BLOCKER (C6): emergency contacts.** The safety card needs numbers we have verified (police 999, MOHRE 80084, and
   the human-trafficking and shelter hotlines). I won't guess numbers; please confirm the list or name a source.
8. **DECISION (C3): when to offer a case.** **Recommendation:** the Guide sets `offer_case` and code shows the offer card
   at most once every 3 turns, never starts a case without a tap, and never pushes when the worker only asked a general question.
9. **DECISION (C4): contract text cap** (see 3.7): about 20,000 characters for contracts, against the free-tier token budget.
10. **RISK: more surface for prompt injection.** Every worker message, chip label and contract text is wrapped in
    `<<<WORKER_DATA>>>`; the Guide can't call tools or change routes, code does. Eval covers injection in chat and in contracts.
11. **RISK: translation quality.** The question bank, starter chips and cards add about 120 strings × 7 languages.
    As in 6.3, drafts are generated and marked for native review; the pilot should include one reviewer per pilot language.

## 5. Sprints

Sizes assume your earlier pace (S = ~2 h, M = ~4 h, L = ~a day).

### C0 — Clickable prototype first (S)
*25 Oct, your choice:* the prototype is built on Lovable for the Sheraa ideathon pitch (docs/demo/LOVABLE_PROMPT.md).
Its Ask answers come from the new `POST /v1/demo/ask` (real retrieval, citation and money checks in code, CHANGES.md 28);
its Case door uses the existing `/v1/cases` endpoints. The Contract X-ray is scripted.
*25 Oct, your choice:* built in this repo instead of Lovable: https://haqqi-ai.vercel.app/demo (`frontend/app/demo`,
`frontend/components/demo/`), separate from the main flow. Add `?presenter=1` for the presenter keys.

- [ ] **C0.1 Mocked chat prototype**: the empty state, Ask, Contract and Case doors, facts card, result cards, with
      canned responses (no backend), in Hindi, Urdu and English.
      Check: tried on a real phone by you and 2–3 workers or a volunteer; notes in `docs/chat_ux_notes.md`. Ports: new.
      *Why first:* it's the cheapest way to learn which door people tap and whether chips beat typing, before building.

### C1 — Conversation backend + Ask door (M)
- [ ] **C1.1 `chats` table + migration 0003**, 7-day expiry in the existing purge job, `DELETE /v1/chats/{id}`.
      Check: migration on a fresh DB; purge test with an 8-day-old chat; delete test.
- [ ] **C1.2 Models**: `ChatMessage` (role, text, cards, chips), `GuideReply`, `ChatView`.
      Check: round-trip JSON test; `mypy --strict`.
- [ ] **C1.3 Guide prompt** `haqqi/rag/prompts/guide.md` (intent, short answer in the worker's language, cite only given
      chunk ids, no amounts, labour-law scope, offer_case rule). Recorded in `CHANGES.md` for your review.
      Check: snapshot test; you approve CHANGES.md.
- [ ] **C1.4 `POST /v1/chats`, `POST /v1/chats/{id}/messages` (SSE), `GET /v1/chats/{id}`**: safety check → retrieve →
      Guide → `enforce_citations` → amount guard → store. Rate limits: 30 messages / 10 min per IP, 40 turns per chat.
      Check: API tests with a scripted LLM: fabricated article dropped; reply with "AED 5,000" rejected then retried;
      no citations left → "not sure" + 80084; injection text in a message doesn't change the intent.
- [ ] **C1.5 Live check** on 10 real questions (EN/HI/UR): passport, overtime, probation, sick leave, resign without
      notice, late salary, deductions, contract renewal, gratuity rule, visa question (→ redirect).
      Check: `docs/chat_probe.md` with answers and citations; ≥ 8/10 correct and cited (by eye).

### C2 — Chat UI shell (M)
- [ ] **C2.1 Screen + routing**: `/[lang]` becomes the chat; `ChatScreen`, `MessageList`, `MessageBubble`, `Composer`
      (text, 🎤 reusing `VoiceInput`/`recorder.ts`, 📷), typing indicator, resume prompt, Delete my chat.
      Check: Playwright at 375 px (Pixel 7 + iPhone profiles), no sideways scroll, RTL in /ur and /ar, ≥ 44 px targets.
- [ ] **C2.2 Empty state**: greeting, three door cards, three example-question chips per language.
      Check: catalog test keeps every language on the English key set.
- [ ] **C2.3 Article chip + law sheet**: tap → bottom sheet with the clause text in English and Arabic (`GET /v1/law/{chunk_id}`).
      Check: unit test; browser run.
- [ ] **C2.4 Voice in the chat**: a voice message sends straight away with an "edit" option on its bubble.
      Check: Pixel 7 fake-mic run (Hindi clip) and your iPhone.

### C3 — Case door in the chat (L)
- [ ] **C3.1 Question bank**: one question + chips per missing field (emirate, zone, worker type, still employed,
      start month/year, end month/year, basic, total, months unpaid, notice), in 8 catalogs.
      Check: test that every `MISSING_FIELDS` entry has a question and every chip maps to a valid enum value.
- [ ] **C3.2 Slot filling**: code merges `facts_update`/chip answers, runs `route_case`, asks the next question;
      out of scope → the existing referral as a card, mid-conversation.
      Check: scripted tests for TC-01, TC-07 (DIFC → referral), TC-18 (story already has everything → straight to facts card).
- [ ] **C3.3 Offer card** (flag 8) and **facts card** (Intake over the transcript, then PATCH on confirm; ✎ opens `ConfirmForm` sheet).
      Check: TC-02 via chips reaches the same `CaseFacts` as the form path (equality test).
- [ ] **C3.4 Run the pipeline inline**: progress as a message (reuse `sse.ts`), then `VerdictCard`, `ClaimCard`,
      `NextStepsCard`, `ComplaintCard` (split from `results.tsx`).
      Check: TC-02 in Urdu through the chat → **6,229.59**, same citations as the form path; phone run, screenshot in `docs/screens/`.
- [ ] **C3.5 Follow-up questions** over the `Analysis` (explain, never recalculate).
      Check: "why is my gratuity 3,229.59?" answered with Art. 51 and the formula; reply with a new amount is rejected.

### C4 — Contract door (L)
- [ ] **C4.1 Upload + extraction** (flag 2): up to 4 photos (compressed on the phone to ~300 KB each) or pasted text;
      images not stored. Check: size/type limits (413/415); a test log grep finds no contract text.
- [ ] **C4.2 Redaction** before the LLM. Check: unit tests with sample passport, Emirates ID (784-…), labour card, phone.
- [ ] **C4.3 Contract reader prompt + red-flag rules in code** with article ids verified against `data/law`.
      Check: 6 sample contracts (2 MOHRE standard, 2 offer letters, 1 free zone, 1 with planted red flags) → summary
      fields correct, every planted red flag found; samples are synthetic, no real people.
- [ ] **C4.4 Contract card + "use these details"** → pre-fills the case door.
      Check: the sample contract's wage, start date and notice appear on the facts card.

### C5 — Listen and accessibility (S)
- [ ] **C5.1 ▶ Listen** on every Haqqi message (flag 4), "read answers aloud" toggle, speed control.
      Check: voice coverage table per language on your iPhone and one Android phone in `docs/language_check.md`.
- [ ] **C5.2 Large text toggle**, high-contrast check, screen-reader labels on chips and cards.
      Check: Lighthouse accessibility ≥ 95 on the chat screen.

### C6 — Safety and limits (S)
- [ ] **C6.1 Emergency card** (flag 7): code keyword check in 8 languages plus the Guide's `safety` flag.
      Check: table test with 16 phrases (2 per language), and 10 ordinary messages that must not trigger it.
- [ ] **C6.2 Off-topic and abuse**: polite refusal, turn cap, per-IP limits; story/message caps as today.
      Check: tests; a 41st turn → "start a new chat".

### C7 — Chat evaluation (M)
- [ ] **C7.1 `eval/chat_cases.jsonl`**: 40 Ask questions (expected articles, must-not-say), 12 intent/escalation
      dialogues, 6 contracts, 6 injection/safety cases, across the 8 languages.
- [ ] **C7.2 `make eval-chat`** metrics: intent accuracy ≥ 90%; cited answers 100%; supported citations ≥ 90%;
      amounts from the LLM 0; red-flag recall ≥ 90%; **escalation precision** ≥ 90% (a general question is not pushed
      into a case); safety card recall 100%; p95 turn latency < 8 s on Gemini.
      Check: table printed and saved to `eval/results/chat-<date>.json`; README gets a chat row.
- The existing 50-case pipeline eval keeps running unchanged (the pipeline is unchanged).

### C8 — Pilot (M, then 2 weeks of running it)
- [ ] **C8.1 Privacy-safe analytics**: counts only (door chosen, turns, voice vs text, case started, complaint
      downloaded, 👍/👎 per answer), no text, in Langfuse metadata or a `chat_events` table.
- [ ] **C8.2 Feedback**: 👍/👎 on every answer, "was this clear?" after results, optional 1-tap "did you file?" on return.
- [ ] **C8.3 Volunteer mode** (optional): "I am helping someone" switch; same flow, copy says "the worker".
- [ ] **C8.4 Run the pilot**: 20–30 workers through 1–2 community helpers, in 3–4 languages, using the PRD's
      interview questions. Check: `docs/pilot_report.md` with the numbers below and quotes (with permission, no names).

**Pilot success measures:** ≥ 70% of conversations get a useful first answer in < 10 s; ≥ 50% use voice at least once;
of workers who start a case, ≥ 60% reach the verdict; 👍 rate ≥ 80%; 0 amounts from the LLM; 0 PII in logs.

## 6. Suggested order and cut list

C0 → C1 → C2 → C3 is the core (a working chat with Ask + Case). C4 (contracts) is the most new risk and can follow.
If time runs short, cut in this order: volunteer mode → large-text toggle → WhatsApp share → contract photos
(keep pasted text) → TTS. **Never cut:** citation enforcement, the no-LLM-amounts guard, the safety card, the eval.

## 7. Open questions to settle in C0

- Which door do workers tap first? If most tap "something went wrong", the case door deserves the top slot.
- Do workers prefer chips or speaking for dates and amounts?
- Is a voice greeting welcome or annoying in public (on a bus, at a camp)? Default it off, or on?
- Will workers photograph a contract in front of a stranger's app? The answer decides how much effort C4 deserves.
