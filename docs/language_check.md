# Language check (task 6.3)

One harness case per language, run end to end through the API the way the UI does (create → confirm → analyze →
complaint PDF) by `eval/language_check.py`. Run on 4 Oct 2026 on a local server with the **free Gemini models only**
(K2 off) and the BGE-M3 law index. Raw results: `eval/results/language_check.json`; PDFs: `docs/language_check/`.

**What is checked here:** route, the issues the Intake found, totals against the hand-worked figures, citations, whether
the worker-facing text and the letter translation are in the worker's script, digits, PDF fonts. **What is not:**
fluency and tone. That needs a native or fluent reader (last column).

## Results

| Case | Language | Route | Issues found (expected) | Total AED | Citations | Worker's script | PDF fonts | Time | Native/fluent reader |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-01 | Hindi | ready | unpaid_wages (unpaid_wages) | 5,400.00 ✓ | Art. 22(2) | 95% | Devanagari ✓ | 42 s | |
| TC-02 | Urdu | ready | termination, notice_pay (same) | 6,229.59 ✓ | Art. 43(2), 43(3) | 97% | Nastaliq ✓ | 49 s | |
| TC-03 | English | ready | gratuity (gratuity) | 16,056.85 ✓ | Art. 42(3), 51(2/3/5/7) | 100% | Sans ✓ | 26 s | |
| TC-04 | Malayalam | ready | illegal_deduction (same) | 2,400.00 ✓ | Art. 25(1), 39(1) | 95% | Malayalam ✓ | 37 s | |
| TC-05 | Tagalog | ready | document_retention (same) | 0.00 ✓ | Art. 13(2) | 100% | Sans ✓ | 26 s | |
| TC-06 | Bengali | ready | overtime, leave (same) | 0.00 ✓ | CR 15(3); Art. 17(1), 19(2), 29(1), 29(8) | 96% | Bengali ✓ | 16 s | |
| TC-08 | Nepali | out of scope → domestic referral ✓ | – | – | – | – | no PDF (referral) | 12 s | |
| TC-23 | Arabic | ready | unpaid_wages (same) | 5,000.00 ✓ (max 5,000) | Art. 22(2) | 100% | Naskh ✓ | 34 s | |

- **Totals:** every one matches the hand-worked figure (CASES.md, harness `max_total`).
- **Writer:** it never failed.
- **Facts paragraph:** no Arabic-Indic digits in any letter.
- **Worker's script:** the 3–5% outside the worker's script is fixed Latin text such as "AED" and "MOHRE".
- **Totals of 0.00 are expected:**
  - TC-05 (passport kept) has no money claim.
  - TC-06 has no overtime rule in the calculator (the PRD table has none), and leave is paid only when a job ends
    (flag 5).

## Findings for 6.4

1. **TC-02 (Urdu): the explanation contradicts the claim (serious).**
   - The Analyst put this in `not_covered`: "not entitled to end-of-service gratuity because they have not completed one
     year of continuous service". The service was 2024-06-01 → 2026-09-20, which is 842 days.
   - The Writer repeated it to the worker in Urdu: "Haqqi can't help with your gratuity claim because your service is
     less than one year".
   - The same page shows gratuity AED 3,229.59 from the calculator.
   - The model got the service length wrong; the calculator didn't. Earlier runs of the same case were right, so this
     is intermittent.
2. **TC-01 (Hindi): over-promising tone.**
   - The headline says "Hello friend, we will fully help you get your withheld salary back".
   - The explanation says "we will help you through this complaint letter… we are with you in this process".
   - Haqqi prepares a complaint; it doesn't recover money or accompany the worker.
3. **TC-06 (Bengali): vague headline.** "Information about your work rights and dues" doesn't say what is wrong.
4. **Not checked yet:** the Nepali letter, because TC-08 is a referral and makes no PDF. A Nepali mainland case would
   check the Devanagari PDF path for `ne`.

## Reader notes

Add notes per language here: anything unnatural, wrong or hard to understand in the explanation, checklist, UI text or
letter translation.

| Language | Reader | Notes |
| --- | --- | --- |
| | | |
