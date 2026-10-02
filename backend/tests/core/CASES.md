# Calculator cases, worked by hand (task 3.2)

Rules (docs/IMPLEMENTATION_PLAN.md flags 2–6):
- Daily basic wage = basic ÷ 30. Daily total wage = total ÷ 30.
- Service days = end − start + 1 − unpaid absence days (both ends inclusive).
- Years = days ÷ 365. Gratuity eligibility needs ≥ 365 days.

**Gratuity (Art. 51)**
- 21 days' basic wage for each of the first 5 years, 30 days for each year after that. Part years count pro rata.
- Capped at 2 years' basic wage (24 × basic).
- Part-time (CR 1/2022 Art. 30): the capped full-time amount × weekly hours ÷ 48.
- Flexible contracts: not calculated, "ask MOHRE". Only due once the job has ended.

**Other lines**
- **Unpaid wages (Art. 22(2)):** months unpaid × total monthly wage.
- **Notice pay (Art. 43(3)):** (contract notice clamped to 30–90 days − days given) × daily total wage.
  - Employer ended the job: a claim line.
  - Worker resigned: a separate "worker owes" line, not deducted from the claim.
- **Deductions (Art. 25):** the full amount the worker reports. A note is added if the monthly deduction is over 50% of the wage.
- **Leave (Art. 29(9), CR Art. 19(2)):** only once the job has ended. Unused days × daily basic wage.
  - Unknown day count → "not calculated".
- **Rounding:** each line is rounded ROUND_HALF_UP to 0.01. The total is the sum of the rounded lines.

## TC-01: Hindi, still employed, 3 months unpaid
Basic 1,200, total 1,800, start 2023-02-01, still employed.
- Unpaid wages: 3 × 1,800 = **5,400.00**
- Gratuity: not due (still employed).
- **Total 5,400.00**

## TC-03: English, resigned after ~6 years, gratuity check
Basic 3,500, total 5,000, 2020-08-01 → 2026-08-31, resigned with 30 of 30 notice days served.
- **Service days.** 2020-08-01 → 2026-08-01 is 6 × 365 + 1 leap day (29 Feb 2024) = 2,191 days.
  Add 30 days to 31 Aug, then +1 for both ends inclusive: **2,222 days**.
- **Years.** 2,222 ÷ 365 = 6.087671…
- **Gratuity days.**
  - 5 × 21 = 105
  - 1.087671… × 30 = 32.630137…
  - Total: 137.630137 days
- **Daily basic.** 3,500 ÷ 30 = 116.6667
- **Gratuity.** 137.630137 × 116.6667 = 16,056.849… → **16,056.85**. The cap of 24 × 3,500 = 84,000 isn't reached.
- **Notice.** Shortfall 0, so the worker owes nothing.
- **Total 16,056.85.** The employer's offer of 6,000 is low.

## TC-02: Urdu, terminated the same day, 30-day notice
Basic 2,000, total 3,000, 2024-06-01 → 2026-09-20, employer terminated, 0 notice days given.
- **Service days.** 2024-06-01 → 2026-06-01 is 730 days (no 29 Feb in between). Add 111 days to 20 Sep, +1: **842 days**.
  842 ÷ 365 = 2.306849 years.
- **Gratuity.** 2.306849 × 21 = 48.443836 days × 66.6667 = 3,229.589… → **3,229.59**
- **Notice.** 30 × (3,000 ÷ 30) = **3,000.00**
- **Total 6,229.59**

## TC-19: terminated after 8 months, no notice
Basic 3,000, total 4,500, 2026-01-05 → 2026-09-10, employer terminated, contract 30 days, 0 given.
- **Service.** 249 days (< 365), so no gratuity: line 0.00 with the reason.
- **Notice.** 30 × 150 = **4,500.00**
- **Total 4,500.00**

## TC-20: 28 years, cap hit, 90-day notice, August unpaid
Basic 20,000, total 30,000, 1998-01-01 → 2026-08-31, employer terminated, 90 days' notice, 0 given, 1 month unpaid.
- **Service days.** 10,470 (1998-01-01 → 2026-08-31 inclusive). 10,470 ÷ 365 = 28.684932 years.
- **Gratuity days.** 105 + 23.684932 × 30 = 105 + 710.547945 = 815.547945
- **Uncapped gratuity.** 815.547945 × 666.6667 = 543,698.63
- **Capped.** 24 × 20,000 = **480,000.00**
- **Notice.** 90 × 1,000 = **90,000.00**
- **Unpaid wages.** 1 × 30,000 = **30,000.00**
- **Total 600,000.00.** Above the 50,000 MOHRE decision limit.

## TC-21: resigned with full notice; July salary and gratuity unpaid
Basic 4,000, total 6,000, 2022-03-01 → 2026-07-31, resigned, 30 of 30 notice served, 1 month unpaid.
- **Service days.** 1,614. 1,614 ÷ 365 = 4.421918 years.
- **Gratuity.** 4.421918 × 21 = 92.860274 days × 133.3333 = 12,381.369… → **12,381.37**
- **Unpaid wages.** 1 × 6,000 = **6,000.00**
- **Total 18,381.37**
- Note: the n8n harness expected ≤ 18,366, because it used (end − start) ÷ 365.25. Our whole-day rule (flag 3)
  gives a slightly higher figure. The Sprint 7 eval row uses this number.

## TC-22: still employed, leave refused, no money
Basic 5,000, total 7,000, still employed, issue `leave`. No money lines: leave is paid only once the job ends.
**Total 0.00**

## Edge cases
- **Exactly 1 year.** 2025-01-01 → 2025-12-31 is 365 days, so eligible: 1 × 21 × (3,000 ÷ 30) = **2,100.00**
- **1 day short.** 2025-01-02 → 2025-12-31 is 364 days, so not eligible: **0.00**
- **Exactly 5 × 365 days.** 2021-01-01 → 2025-12-30 is 1,825 days = 5.0 years: 105 × 100 = **10,500.00**
- **5 calendar years.** 2021-01-01 → 2025-12-31 is 1,826 days (one leap day) = 5.00274 years.
  105 + 0.00274 × 30 = 105.082192 days × 100 = **10,508.22**. A consequence of the days ÷ 365 rule.
- **Part-time.** TC-03 with a 24 h/week contract: 16,056.849… × 24 ÷ 48 = 8,028.424… → **8,028.42**
- **Unpaid absence.** 2025-01-01 → 2026-01-20 is 385 days. Minus 30 absent days = 355, so not eligible: **0.00**
- **Notice clamp.** A contract notice of 14 days counts as the legal minimum of 30. A notice of 120 counts as 90.
- **Resigned without notice.** Total 3,000, contract 30, 10 days given: the worker owes 20 × 100 = **2,000.00**, as a
  separate line. It is not subtracted from the claim.
- **Deductions.** TC-04: 600/month for 4 months = **2,400.00** reported. 600 is 20% of 3,000, so no 50% note.
  1,800 of 3,000 a month would get the note.
- **Leave at the end of a job.** 12 unused days × (3,000 ÷ 30) = **1,200.00**. Unknown day count → "not calculated".
