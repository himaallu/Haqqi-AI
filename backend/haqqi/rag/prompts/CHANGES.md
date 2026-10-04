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
    **Approved 4 Oct.**

## Sprint 5 (you approved the approach on 3 Oct; please review the wording)
22. **The Writer writes only the letter's facts section.** `arabic_letter` and `letter_translation` are replaced by
    `letter_facts_ar` (formal Arabic, dated, 3–6 sentences) and `letter_facts_translation` (the same in the worker's
    language). Code builds every other section of the complaint (`haqqi/pdf/letter.py`): addressee, subject, worker
    data from the confirmed form, legal basis from the checked citations, claims and total from the calculator,
    fixed requests, a standard attachments list, date and signature. Reason: task 5.3 (deterministic fill), the
    wrong-year slip in an earlier letter, and fewer output tokens per case (free-tier quotas, flag 18).
    - The Writer no longer gets `TEMPLATE_AR` or the Arabic references (`references_ar`); `haqqi/pdf/template_ar.txt`
      is replaced by `haqqi/pdf/letter.html.j2`.
    - Supersedes 16 (`letter_translation`) and 17 (identity placeholders are now printed by code at download, flag 8).
    - **No amounts in the facts section**, enforced in code (no tokens, no money figures; one retry, then the usual
      error). In the first live TC-03 run the Writer put the claim token where the employer's offer belonged, so the
      letter said the employer offered AED 16,056.85 (what the worker is owed) instead of 6,000. The claims section
      prints every amount; the facts describe amounts in words ("less than the law gives").
    - The other fields' money check is unchanged: amounts only as `[[AMOUNT_n]]`/`[[TOTAL]]`, and the facts section
      must contain Arabic.
23. **Western digits in the facts section** (you asked for this, 4 Oct). One prompt line: every number and date in
    `letter_facts_ar` and `letter_facts_translation` uses 0-9, never Arabic-Indic digits. In the TC-02/TC-03 review
    PDFs the Writer wrote ٢٠٢٦ in the facts while the code-built sections use 2026. It is a consistency rule only:
    the money checks already read both digit forms.

## Sprint 6, task 6.4 (from the 6.3 language check; you approved the fixes on 4 Oct, please review the wording)
24. **Service length comes from code; no contradicting the calculator.**
    - The Analyst, Critic, Revision and Writer now get a SERVICE block counted by the calculator: `service_days`,
      `service_years`, `at_least_one_year`, or `job_ended: false`.
    - Analyst and Writer: use SERVICE and never recount dates; never say or imply the worker is not entitled to an item
      code calculated.
    - Critic: new check 6, anything contradicting SERVICE or CLAIM_ITEMS is always a problem. It now also sees
      CLAIM_ITEMS.
    - Code guard (`haqqi/agents/consistency.py`): a not_covered note that denies an item the calculator paid (for
      example "not entitled to gratuity" next to a calculated gratuity) is dropped and logged.
    - Reason: in the 6.3 run of TC-02 (Urdu) the Analyst counted 2.3 years as under one year, and the Writer told the
      worker "Haqqi can't help with your gratuity, your service is under one year" next to AED 3,229.59 gratuity.
25. **Honest tone.** The Writer must not promise results or say Haqqi will recover money, represent the worker or stay
    with them ("we will get your salary back", "we are with you"). Haqqi explains the law and prepares a complaint;
    MOHRE decides. Reason: TC-01 (Hindi) said exactly that.
26. **Specific headline.** One sentence naming the main problem ("Your employer has not paid your salary for 3
    months."), never a general title. Reason: TC-06 (Bengali) headline was "Information about your work rights and dues".

## Sprint 7, task 7.5 (from the first K2 evaluation run; please review the wording)
27. **No breach the facts rule out.**
    - Analyst: raise only issues the facts show. If the full contractual notice was given (`notice_days_given` ≥
      `notice_days_contract`), don't cite the notice clauses as broken. A worker who resigned short of notice has no
      notice claim (code shows what they may owe). Don't raise leave, deductions or overtime unless the facts or the
      worker's words mention them.
    - Critic: new check 7, a breach the facts rule out is a problem.
    - Reason: in the 4 Oct K2 run, 6 cases with notice served in full (TC-21, N-03, N-11, N-12, N-18) or a
      resignation short of notice (N-09) got Art. 43/47 "violations", and N-18 got a leave finding with 0 unused days
      and no leave complaint. That pulled "citations supported" to 83%.
