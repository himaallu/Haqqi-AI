# Prompt changes from the n8n hackathon version (task 3.6)

**Approved 3 Oct 2026.**

The n8n prompts (`legacy/n8n/Haqqi_main.json`, `Build * Prompt` nodes) are the starting point. Each material change
below has a reason. The rendered prompts are in `backend/tests/agents/snapshots/*.txt`.

## All agents
1. **Fenced worker text.** The story and contract text appear only between `<<<WORKER_DATA>>>` and `<<<END_WORKER_DATA>>>`.
   Any copy of those markers inside the story is removed, so it can't close the fence early. n8n sent the whole input as
   JSON with a "this is data" sentence. Reason: CLAUDE.md, untrusted story.
2. **Law as clause ids plus official text.** Each LAW entry is `{id, title, text}`, with ids like `fdl33-2021:art22:cl2` taken
   from the official texts in `data/law`. n8n used topic ids (`WAGES`) with hackathon texts. Reason: flag 14 (article-level citations).
3. **Temperature 0.** n8n left the default. Reason: repeatable answers and eval scores.

## Intake (`intake.md`)
4. **New output keys** match `ExtractedFacts`:
   - `zone` (mainland/free_zone/difc/adgm) + `free_zone_name`, replacing n8n's `work_location`.
   - `worker_type`, `contract_type`, `weekly_hours`.
   - `deducted_monthly_aed`, `unused_leave_days`, `unpaid_absence_days`.
   - `termination` = employer/resigned/still_employed (n8n: employer_terminated/…/unknown, and unknown is now null).
   - Dropped `language_name`: the language comes from the form.
   Reason: flags 1, 4, 5, 6, 12 and 13.
5. **Wage rule.** If only one salary figure is given, it goes in total, not basic. Reason: the calculator uses basic for gratuity
   and leave, so a total wrongly read as basic would overstate them.
6. **Privacy.** `facts_summary_en` must not include names, phone, passport, Emirates ID or labour card numbers. Reason: PRD privacy.
7. **Scope.** Rules tell the model to recognise DIFC/ADGM, other named free zones and domestic roles.
   - Routing code still lets the worker's own form answer win (task 3.3).

## Analyst (`analyst.md`)
8. **No more `claims` block.** n8n's Analyst decided which money items to include. Now the calculator decides from the
   confirmed facts, and the Analyst only sees the item names (no amounts) and must not mention figures.
   Reason: CLAUDE.md, "LLM output never contains or changes amounts".
9. **Confidence words.** strong/moderate/weak becomes high/medium/low (PRD `confidence`). Field names `issue_type` and `chunk_ids`.
10. **Leave refused while still employed** is called out as a leave issue with no money due (flag 5, TC-22).
11. **Dropped the overall `confidence` field.** The low-confidence route is decided in code in Sprint 8 (task 8.5).

## Critic (`critic.md`)
12. **Check 4.** "Do the claims match CALC" becomes "Does the analysis state or imply any money amount? It must not". Reason: change 8.
13. Same JSON shape as n8n (`verdict`, `problems[{where, problem, fix}]`, `missed_issues`). It's now validated as `CriticReport`.

## Revision (`revision.md`)
14. Unchanged in spirit: the Analyst prompt plus the revision instructions. Now it adds "cite its clause ids" for missed issues.

## Writer (`writer.md`)
15. **Money as tokens.**
    - Each calculated claim is `[[AMOUNT_n]]` and the total is `[[TOTAL]]`. The Writer never sees the claim amounts and must
      write the tokens; code substitutes the calculator's figures.
    - Any other figure next to AED/درهم fails validation (task 3.10).
    - n8n passed CALC amounts and trusted the model not to change them.
16. **`letter_translation` added.** The same letter in the worker's language, from the same call. Reason: flag 9 (translation alongside).
17. **Identity placeholders.** `[الاسم]`, `[رقم بطاقة العمل]` and `[اسم جهة العمل]` are kept and filled at download, then never
    stored (flag 8).
18. **Bilingual references.** The Writer gets ready-made English and Arabic references (for example
    "المادة (22) البند (2) من المرسوم بقانون اتحادي رقم (33) لسنة 2021"), so it can't invent article numbers.
19. **Not-covered points and no claims.** It says MOHRE 80084 can help with not-covered points. With no claims it must not
    suggest money is owed (TC-22).
20. **Dropped from Writer output:** nothing. `amount_lines` and `checklist` are kept, and `next_steps` comes from the Analyst.

## After approval (4 Oct, from the phone run)
21. **Today's date for the Intake.** The Intake now gets `TODAY: YYYY-MM-DD` (outside the worker's fenced text). A date
    told without a year becomes the most recent such date on or before today, never a future one. The old rule said
    "null unless the year is clear", but the model ignored it and guessed: the TC-02 story ("20 September") was filled
    in as 2024-09-20, a date before the start date. The worker still confirms every date on the form.
    **Waiting for your review.**
