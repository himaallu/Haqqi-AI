# Haqqi Chat — Desk research findings

24 Oct 2026. Companion to docs/CHAT_PLAN.md and docs/CHAT_UX_RESEARCH.md (Part 3, step A, done as desk research).
What this covers: official UAE channels and rules that shape the product, evidence on why workers don't file,
design research on low-literacy and voice interfaces, phones and languages, and a check of our law index
against what workers ask. What it **can't** cover: real users. Interviews and the C0 prototype test are still needed
(section 9).

**How sure we are.** Each fact is tagged: **[official]** = a UAE government page or ILO report; **[reviewed]** =
an NGO guide reviewed by a law firm; **[press]** = news or law-firm/vendor blogs, to verify before it goes into the
app; **[study]** = peer-reviewed or workshop research.

## 1. The ten findings that matter most

1. **Workers frame problems as stories, not legal terms.** In a 2025 study with 15 low-literate workers in India, a
   voice-first chat took **49 s** on average to reach an answer versus **118 s** for the government's form app; only
   **2 of 9** form users finished unaided, and **6 of 15** couldn't use the form app at all because of language.
   Nobody used the search box, because it assumed they knew scheme names. **[study]**
   → Confirms the chat direction. The empty screen should invite a story ("Tell me what happened"), not a topic picker.
2. **Text is unusable for first-time low-literacy users; graphics + voice work, and a consistent help feature matters.**
   Spoken dialogue was fastest for people comfortable with speech. **[study, Medhi et al.]**
   → Icons on the door cards and chips, ▶ on every answer, one help button that is always in the same place.
3. **Voice needs a clear "I'm listening" state.** The study's main voice problem: users weren't sure the app was
   listening. Offline TTS voices without local accents were hard to understand; **text shown next to the audio rescued
   it**. **[study]**
   → Big animated recording state with a timer (we have the timer), and never audio without its text.
4. **MOHRE's own channels are large and already digital.** 600 590 000 is the 24/7 call centre; **80084** is the Labour
   Claims and Advisory Centre; international +971 6 803 4000. **[official]** WhatsApp runs on 600 590 000 **[reviewed]**.
   MOHRE's Tawasul system handled about **60 million** interactions in 2025, about **1.2 million** of them through chat,
   email, social media and WhatsApp. **[press, quoting MOHRE]**
   → Haqqi should hand off to these channels, not imitate them. "Message MOHRE on WhatsApp" can link to 600 590 000.
5. **There is a confidential salary complaint.** MOHRE's "My Salary Complaint" lets a worker report late or unpaid pay
   without the employer learning who filed it. It covers pay more than 15 days late, 1–2 months unpaid, unpaid overtime
   and unlawful deductions. It needs registration with MOHRE (Emirates ID, labour card, UAE Pass). **[official service page; details press]**
   → For a worker who is **still employed and afraid**, this is the most useful next step we can offer, and today's
   results page doesn't mention it. Add it to next steps for unpaid-wage cases.
6. **The Wage Protection System (WPS) doesn't catch individual cases.** An employer counts as compliant if at least 80% of
   workers get at least 80% of their registered wage through the WPS. So one underpaid worker is invisible unless they
   complain. If an inspector's correction order (7–14 days) is ignored, the worker can **transfer to another employer
   without notice** and can reportedly be compensated through **insurance**. Only 4 free zones run mandatory WPS
   (JAFZ, DMCC, TECOM, KEZAD); about 1 million free-zone workers may be outside it (estimate). **[official: ILO 2025]**
   → An Ask answer to "my salary is late" should explain this: "MOHRE may not know unless you report it."
   The transfer right is a strong, reassuring fact for a worker afraid of losing their visa.
7. **Fear is the barrier, and absconding reports are the threat.** Fear of employer reprisal and deportation recurs in
   HRW and ILO work **[official/NGO, some dated]**; ILO 2025 adds that workers lack the resources, language skills,
   money or time for separate proceedings. Employers can file "absconding" reports. Per legal blogs, an employer can't
   file one while the worker has a pending complaint, and bad-faith reports carry fines **[press]**.
   → A "Will I get in trouble?" answer and a fear-aware tone matter as much as the law. The facts in it need checking
   with a UAE lawyer before they go in the app (flag R2).
8. **Our law index already covers almost everything workers ask about**: contract copy in your language, probation,
   hours, overtime, rest days, sick leave, annual leave, maternity, notice, gratuity, deductions, recruitment fees,
   passport and job transfer (section 6). **The gaps are around the law:** the unemployment insurance law (ILOE,
   FDL 13/2022), emirate health insurance rules, the WPS resolution (MR 598/2022), absconding rules and MOHRE's
   service procedures.
9. **Most likely users by number:** India (~4.4 M residents), Pakistan (~1.9 M), Bangladesh (~0.8 M), the Philippines
   (~0.8 M) and Nepal (~0.4 M), out of about 10 M expatriates. **[press, compiled estimates; no official breakdown found]**
   → Our 7 languages match. Workers from Pakistan may prefer Pashto or Punjabi to Urdu: ask in interviews, don't assume.
10. **Text-to-speech in the phone is probably enough to start.** Google's Android TTS lists Bangla, Filipino,
    Malayalam, Nepali and Urdu (and Hindi); voices may need a download and vary by device. **[official: Google support]**
    → Supports CHAT_PLAN flag 4: browser voices first, show ▶ only when a voice exists, measure on real phones.

## 2. Official channels and services (for the app's "get help" content)

| What | Detail | Source tag |
| --- | --- | --- |
| MOHRE call centre | 600 590 000, 24/7 | [official] |
| Labour Claims and Advisory Centre | 80084 (already used everywhere in Haqqi) | [official] |
| International | +971 6 803 4000 | [official] |
| WhatsApp | 600 590 000 ("+971 600 590 000"); also offers video-call consultations | [reviewed] + [press] |
| My Salary Complaint | confidential; MOHRE app or website; Emirates ID, labour card, UAE Pass | [official page] + [press] |
| Complaint tracking | MOHRE app, website, WhatsApp, 80084 | [press] |
| Police emergency | 999 | well established |
| Human trafficking hotline | **800 SAVE (800 7283)**, 24/7; Ewa'a shelters | [official: u.ae, MOFA] |
| Dubai Foundation for Women and Children | 800 111 per a 2019 list: **not confirmed as current** | [press, dated] |

The MOHRE contact page returned 503 when fetched today; the numbers above come from its indexed listing. Check the
page once more before the safety card ships (CHAT_PLAN flag 7). The emergency card can use 999 and 800 SAVE now.

## 3. Why workers don't file (the PRD's open question)

No source gives a number for "workers who never file". What the evidence does say:
- Fear of reprisal, deportation and job loss (HRW 2006 interviews; ILO studies on early case withdrawal). Dated, but consistent.
- Lack of resources, language, money and time for separate proceedings (ILO 2025, Gulf WPS report).
- Missing evidence and documents (ILO); employers holding passports (illegal under Art. 13(2)).
- Individual wage violations stay invisible to the WPS unless the worker complains (ILO 2025).

**For the pitch:** the WPS finding is the strongest, current, official line: "MOHRE's payroll checks pass any company
paying 80% of its workers 80% of their wage. The rest only get help if they speak up. Haqqi helps them speak up."
The PRD question stays open; asking a consulate welfare desk or an NGO for their intake numbers is the best next step.

## 4. Design research to apply

| Finding | Source | Apply in |
| --- | --- | --- |
| Scenario questions in natural language beat menus and forms; search by name is unused | Prabodhini study 2025 | C0/C2: "Tell me what happened" is the main input; doors are shortcuts, not gates |
| Form jargon fails ("BPL status", "organised sector", "urban/rural"); users suggested "city/village" | same | C3 question bank: "Free zone" → "Is your company in a free zone like JAFZA or DMCC? (Not sure)"; always offer "Not sure" |
| Users unsure whether the app is listening | same | C2: full-width recording state, pulse + timer + "Listening…" text |
| Offline TTS without local accent hard to follow; transcript next to audio rescued it | same | C5: never audio alone; prefer network voices; test each language |
| Likert usability scales failed with low-literate users; a binary questionnaire worked | same | C0 test and C8 feedback: 👍/👎 and yes/no questions only |
| Text-free UIs: semi-abstract graphics + voice; consistent help; text unusable for first-time low-literacy users | Medhi et al. (MSR India) | Icons on doors and chips; one help button in a fixed place |
| Numbers and number pads are familiar even to people who can't read | secondary, on Medhi | Wages and dates can use a number keypad (`inputmode="numeric"`) |
| Quick replies cut typing but get boring; free text needed for nuance | vendor summary of NNGroup + a PMC study | Chips for facts, free text always available |
| An unreliable chatbot (no reply, freezes) destroyed trust in the government app | Prabodhini study | Never a silent failure: show the stage, a retry, and 80084 on any error |
| Guided interviews must be very simple | A2J Author research | One question per message |

## 5. Phones and channels

- WhatsApp penetration in the UAE is about 90% (vendor figures, no DataReportal breakdown found). **[press]**
- Voice notes are common where literacy is low and connections are unreliable (general, not Gulf-specific).
- **No Gulf-specific survey of migrant workers' phone, data or app use was found.** That is a question for the interviews:
  which phone, how much data, WhatsApp vs browser, voice notes vs typing, shared phones.
- WhatsApp beat IVR on completion and cost in a West Africa survey experiment, with slightly lower response. **[study]**
  Supports WhatsApp as the v2 channel (PRD F10).

## 6. Law index coverage against what workers ask

Topics from Migrant-Rights.org's "Know Your Rights: UAE" guide (reviewed by Clyde & Co, Sept 2023) and Gulf News'
"7 illegal practices", checked against `data/law/*.json`:

| Worker question | Article | In our index? |
| --- | --- | --- |
| Do I get a contract copy in my language? | FDL Art. 8, 66 | ✓ |
| How long can probation be? | FDL Art. 9 (max 6 months) | ✓ |
| Is my salary late? When must it be paid? | CR Art. 16, FDL Art. 22 | ✓ |
| How many hours can they make me work? | FDL Art. 17, CR Art. 15 (Ramadan) | ✓ |
| Do I get paid for overtime / rest-day work? | FDL Art. 19, 21 | ✓ |
| Can they cut my salary? | FDL Art. 25 | ✓ |
| How much sick leave do I get, and is it paid? | FDL Art. 31 | ✓ |
| Annual leave and paying out unused leave | FDL Art. 29 | ✓ |
| Maternity, paternity, bereavement leave | FDL Art. 30, 32 | ✓ |
| How much notice must I give / get? | FDL Art. 43 | ✓ |
| Gratuity | FDL Art. 51 | ✓ |
| I paid a recruitment fee / they want visa costs back | FDL Art. 6 | ✓ |
| Can my company keep my passport? | FDL Art. 13(2) | ✓ |
| Can I change jobs? | CR Art. 27 | ✓ |
| Unemployment insurance (ILOE) | FDL 13/2022 | ✗ gap |
| Health insurance (Dubai, Abu Dhabi, other emirates) | emirate laws | ✗ gap |
| My employer filed an absconding case | MOHRE rules | ✗ gap |
| Salary complaint without the employer knowing | MOHRE service | ✗ gap (service, not law) |
| What happens if MOHRE orders payment and they ignore it | MR 598/2022 (WPS) | ✗ gap |

**Recommendation (flag R1):** add a small **"services" knowledge set** (MOHRE service pages: My Salary Complaint,
complaint filing, tracking, absconding withdrawal, ILOE claim), chunked and cited like law but labelled "MOHRE service
information, [date]". Add ILOE (FDL 13/2022) as a law. Leave health insurance out of v1 (emirate-by-emirate and
outside labour law) with a referral line.

### Starter chips (seed the C0 prototype and the C7 Ask eval)

1. "My salary is late" → CR 16, FDL 22 (+ My Salary Complaint)
2. "Can my company keep my passport?" → FDL 13(2)
3. "I paid money to get this job" → FDL 6
4. "How much overtime pay should I get?" → FDL 19
5. "How long is probation?" → FDL 9
6. "I want to leave my job. How much notice?" → FDL 43
7. "How much gratuity will I get?" → FDL 51 (+ calculator, CHAT_PLAN flag 6)
8. "I was sick. Do they still pay me?" → FDL 31
9. "Can I change my company?" → CR 27
10. "My contract is not in my language" → FDL 8, 66

## 7. Changes this suggests for CHAT_PLAN.md (for your approval)

- **R1 (C1, BLOCKER for Ask quality):** the services knowledge set + ILOE law (section 6).
- **R2 (C1):** a lawyer check of the "fear" answers (absconding, retaliation, transfer right) before they ship.
- **R3 (C3 and the current results page):** for unpaid wages with a worker still employed, next steps lead with the
  confidential My Salary Complaint, then the formal complaint. This helps today's flow too, not just the chat.
- **R4 (C2):** the main input says "Tell me what happened, or ask a question"; the three doors become shortcuts under it.
- **R5 (C3):** every question in the bank has a "Not sure" chip and uses everyday words (test each with a worker).
- **R6 (C6):** the emergency card ships with **999** and **800 SAVE (800 7283)**; other numbers only once verified.
- **R7 (C0, C8):** test and feedback forms use yes/no and 👍/👎, never 1–5 scales.
- **R8 (pitch, README):** use the WPS 80/80 finding as the "gap" line (section 3).

## 8. Things I looked for and didn't find

- A number for workers who never file (PRD open question). Still open.
- A Gulf-specific survey of migrant workers' phone and app habits.
- A study of legal-aid chatbots with low-literacy users and voice. The closest are the public-services study above and
  the Stanford Legal Design Lab's work (US users).
- A customer-facing AI assistant from MOHRE. Its 2025 AI work ("Ask Data") is internal.
- Full results of Stanford's user interviews (only summaries were reachable).

## 9. What only real users can answer (interview and C0 checklist)

1. Phone, data plan, shared phone or not; WhatsApp vs browser; voice notes vs typing.
2. Which language they'd choose, and whether Urdu works for Pakistani workers who speak Pashto or Punjabi.
3. "What was the last thing you asked someone about work?" (real chips).
4. Have they heard of My Salary Complaint or 80084? Would they use a confidential complaint?
5. Fear: "What would stop you from complaining?" (and does the transfer-right fact change that?)
6. Would they photograph their contract for an app? (decides C4.)
7. In C0: time to first useful answer, voice vs chips, where they hesitate, yes/no "would you trust this?".

## Sources

Official and research:
- [MOHRE contact page](https://www.mohre.gov.ae/en/contact-us.aspx) (503 when fetched; search listing used), [MOHRE Labour Market Observatory: interaction channels](https://observatory.mohre.gov.ae/en/uae-labour-market-priorities/progressive-workforce-interaction-channels), [MOHRE: My Salary Complaint](https://www.mohre.gov.ae/en/our-services/my-salary-complaint-private-sector-employees-2022.aspx)
- [ILO (2025): Wage Protection Systems in the GCC](https://www.ilo.org/sites/default/files/2025-11/ILO_Beirut_Wage-Protection_Report_R10.pdf), [ILO: Fair recruitment and access to justice](https://www.itcilo.org/sites/default/files/inline-files/Final_ILO%20FRI%20Access%20to%20Justice%20Working%20Paper.pdf), [ILO: Access to justice in South-East Asia](https://www.ilo.org/media/423796/download), [ILO: Employer–migrant worker relationships in the Middle East](https://www.ilo.org/media/420331/download)
- [u.ae: Combatting human trafficking](https://u.ae/about-the-uae/human-rights-in-the-uae/combatting-human-trafficking), [MOFA: Human trafficking](https://mofa.gov.ae/en/The-Ministry/The-Foreign-Policy/Human-Trafficking)
- [First Impressions from Comparing Form-Based and Conversational Interfaces (HCI+NLP 2025)](https://aclanthology.org/2025.hcinlp-1.6)
- [Medhi et al., Text-free UI](https://courses.cs.washington.edu/courses/cse490d/09au/papers/Text-FreeUI.pdf), [Medhi et al., mobile interfaces for low-literacy users (ToCHI)](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/ToCHI2711_Medhi.pdf)
- [Google: languages supported by TalkBack / Google TTS](https://support.google.com/accessibility/android/answer/11101402?hl=en)
- [Ndashimye et al. (2024): WhatsApp vs IVR surveys](https://journals.sagepub.com/doi/abs/10.1177/08944393221111340)
- [HRW (2006): Building Towers, Cheating Workers](https://www.hrw.org/report/2006/11/11/building-towers-cheating-workers/exploitation-migrant-construction-workers-united)

NGO guide (law-firm reviewed):
- [Migrant-Rights.org: Know Your Rights UAE (Sept 2023)](https://www.migrant-rights.org/wp-content/uploads/2023/09/Know-Your-Rights_UAE_as-of-Oct-9.pdf)

Press and secondary (verify before use in the app):
- [Gulf News: MOHRE Tawasul, 60 million interactions](https://gulfnews.com/uae/mohres-ai-powered-tawasul-system-handles-60-million-customer-interactions-in-2025-1.500470770), [Gulf News: secret salary complaint](https://gulfnews.com/living-in-uae/ask-us/what-is-the-secret-salary-complaint-through-mohre-app-1.1657118145936), [Gulf News: salary deducted or late](https://gulfnews.com/living-in-uae/ask-us/salary-deducted-unfairly-or-not-paid-on-time-heres-how-you-can-raise-a-complaint-with-mohre-1.1690470562186), [Gulf News: 7 illegal practices](https://gulfnews.com/living-in-uae/ask-us/workers-rights-in-the-uae-these-7-practices-are-illegal-1.1692786061183), [Gulf News: can my company keep my passport?](https://gulfnews.com/living-in-uae/ask-us/uae-can-my-company-keep-my-passport-1.1608013406067), [Gulf News: false absconding cases](https://gulfnews.com/living-in-uae/ask-us/uae-my-employer-has-filed-an-absconding-case-against-me-what-can-i-do-1.1612360919828), [Mondaq: conditions for absconding cases](https://www.mondaq.com/employee-rights-labour-relations/1115966/what-conditions-should-be-met-for-the-employer-to-file-an-absconding-case), [Gulf News: ILOE uptake](https://gulfnews.com/uae/government/uae-unemployment-insurance-scheme-records-strong-uptake-with-6-8-million-enrolled-1.500120163), [Khaleej Times: emergency numbers (2019)](https://www.khaleejtimes.com/uae/government/complete-list-of-uae-emergency-phone-numbers), [Aletihad: 800 SAVE](https://en.aletihad.ae/news/uae/4594264/javasxript:)
- [ServiceMarket: expatriates by nationality](https://servicemarket.com/en/blog/international-moving-trends-uae), [Wikipedia: Migrant workers in the UAE](https://en.wikipedia.org/wiki/Migrant_workers_in_the_United_Arab_Emirates), [Infobip: WhatsApp statistics](https://www.infobip.com/blog/whatsapp-statistics-2025-global-usage-market-overview), [Lovable guide (quick replies vs free text)](https://lovable.dev/guides/how-to-build-a-chatbot-ui)
