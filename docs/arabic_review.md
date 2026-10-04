# Arabic complaint review (task 5.6)

**Status: waiting for a reviewer.** Task 5.6 is done when a named reader of Arabic signs off below.

## What to review

The PDFs are in `docs/arabic_review/`. Each has the Arabic complaint on the right and the worker's language on the left.

| File | Case | Worker's language | Source of the facts paragraph |
| --- | --- | --- | --- |
| `tc02_ur.pdf` | TC-02: cashier in Abu Dhabi, terminated the same day without notice | Urdu | Live Writer run (Gemini), 4 Oct |
| `tc03_en.pdf` | TC-03: hotel worker in Dubai, resigned after six years, gratuity offer too low | English | Live Writer run (Gemini), 4 Oct |

Regenerated on 4 Oct after the Writer was told to use Western digits (0-9) in the facts paragraph (CHANGES.md 23),
so dates now match the rest of the letter. Totals: TC-02 AED 6,229.59, TC-03 AED 16,056.85.

The name and employer in the samples ("Sample Worker", "Sample Employer LLC") are placeholders. The labour card line is
left blank, which is what the worker sees when they leave a field empty.

## How the letter is built

Only the facts paragraph (أولاً: الوقائع) is written by the model. Everything else is fixed text or comes from code:

- **Fixed text:** addressee, greeting, section headings, requests, attachments list, closing, footer
  (`backend/haqqi/pdf/strings/ar.json`). Change it there and every letter changes.
- **From code:** worker data (from the confirmed form), legal basis (from the checked citations), claims and the total
  (from the calculator), and the date.

So a fix to the fixed text is a one-line change; a problem in the facts paragraph is a prompt change.

## Checklist

For each PDF, please note anything that is wrong, unclear or sounds unnatural.

1. **Tone.** Is it formal and respectful enough for a complaint to MOHRE? Anything too blunt or too flowery?
2. **Correct Arabic.** Grammar, spelling, word choice. In particular:
   - the subject line (الموضوع: شكوى عمالية بشأن …)
   - the claim names (بدل مهلة الإنذار، مكافأة نهاية الخدمة، …)
   - the requests (رابعاً: الطلبات)
   - the law references (المادة (51) البند (2) من المرسوم بقانون اتحادي رقم (33) لسنة 2021)
3. **Facts paragraph.** Does it match the case, with the right dates? Does it read as written by the worker?
4. **Rendering.** Are the letters joined and right to left? Are dates (2024-06-01) and amounts (3,000.00 درهم)
   displayed the right way round inside Arabic sentences?
5. **Completeness.** Is anything missing that MOHRE would expect in such a complaint?
6. **Translation column (if you read it).** Does it match the Arabic?

## Reviewer notes

| # | File | Section | Issue | Suggested fix | Status |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## Sign-off

- Reviewer (name or initials, with permission):
- Date:
- Verdict: approved / approved with the fixes above / needs another round
