# Haqqi Chat — UX research and ideas

Status: **draft for your review**, 24 Oct 2026. Companion to docs/CHAT_PLAN.md.
Part 1 is what similar products do and what to borrow. Part 2 is UX ideas, ranked. Part 3 is how to run our own
research before and during C0. Sources are at the end; most product facts come from the makers' own materials,
so treat the usage numbers as self-reported.

## Part 1 — Reference products and what to take from each

| Product | What it is | Borrow | Avoid |
| --- | --- | --- | --- |
| **MOHRE WhatsApp** (600 590 000, per third-party guides; verify on mohre.gov.ae) | The ministry's own chat: menu-driven consultations, video-call booking, complaint tracking | Hand off to it: "Talk to a MOHRE agent on WhatsApp" as a deep link next to 80084. Haqqi prepares, MOHRE decides | Competing with it. Haqqi's job is the step before: understanding and preparing |
| **Jugalbandi** (Microsoft / AI4Bharat, India) | WhatsApp voice notes → speech-to-text → translate → answer from scheme documents → text-to-speech back | The full voice loop: speak in, *hear* the answer back. Grounded in official documents only | Translating through English loses meaning; we answer in the worker's language directly and check citations in code |
| **Prabodhini vs myScheme** (HCI+NLP 2025 study, 15 low-income users) | Compared a voice-first, RAG chat with a government form app for the same tasks | Direct evidence for our direction: the conversational, voice-first version improved trust and access. Reuse its method (same task, two interfaces, time + completion + preference) for C0 | Small sample; test with our own users |
| **Haqdarshak** (India) | Trained local agents use an app to screen people for welfare schemes, fill forms and follow up | **Helper mode.** Many workers will come through a volunteer, consulate desk or camp organiser. Give helpers a fast flow and a printable summary | Depending only on agents (they say it doesn't scale fast); keep the self-serve path first |
| **Shuvayatra** (Asia Foundation, Nepal) | Safe-migration app for Nepali workers: country guides, about 2,000 articles, videos, podcasts | A small **"Know your rights" library** of short audio + card explainers (passport, overtime, leave, gratuity) for workers who want to browse, not ask | A huge content library to maintain; keep it to 10–15 items tied to our Law Pack topics |
| **Golden Dreams** (Issara Institute) | "Yelp for employers" in Burmese: anonymous peer reviews of employers and recruiters, plus a hotline | Anonymous, peer-to-peer tone; a "get help now" button on every screen | Employer reviews: defamation risk in the UAE and moderation work. Not for v1 |
| **Just Good Work** (Fifty Eight / ETI) | Pre-departure and in-country guidance; works offline; a "new interface for all literacy levels"; document wallet | **Icon-led, low-literacy interface**; offline caching of the rights library; a checklist of documents to keep (payslips, contract photo, ID copies) | Storing documents for the worker (privacy: we keep nothing beyond 7 days) |
| **Gram Vaani / Mobile Vaani** (India) | Voice-only community platform over IVR (missed call → call back), for low-literacy users | Voice as "the lowest common denominator"; later, an IVR or phone-call channel for workers without data | Building IVR in the pilot; note it as v2 alongside WhatsApp |
| **Ulula** (worker voice) | Anonymous multilingual surveys and grievance channels for supply chains | Anonymous **one-tap feedback** after each answer (👍/👎, "was this clear?") as our pilot measure | Their buyer is the employer; ours is the worker. Never share case data with employers |
| **A2J Author** (Chicago-Kent / CALI) | Guided interviews that help people without a lawyer fill court forms; millions of uses | Their research finding: **guided interviews must be very simple**. One question per screen, plain words, progress shown. This is our slot-filling | Pure decision trees can't handle free stories; we keep the LLM for that and the tree for facts |
| **Stanford Legal Design Lab** (AI & Access to Justice) | User research on how people use AI for legal problems; a quality rubric for AI legal answers ("Measuring What Matters", JURIX 2024), used by the Beagle+ chatbot | Use their **rubric to score Ask answers** in C7 alongside our citation checks | — |
| **DoNotPay** (cautionary) | "Robot lawyer"; the FTC fined it in 2025 for claims it never tested, with no lawyers checking quality | Our copy must never say "lawyer" or promise outcomes (CHANGES.md 26 already bans promises). Publish the eval. Get a UAE labour lawyer or legal-aid volunteer to review answers before the pilot | Marketing ahead of evidence |

## Part 2 — UX ideas, ranked for the pilot

**Must have (they shape C0–C3)**

1. **Speak in, hear back.** Tap mic → bubble shows the transcript with "✎ fix" → answer plays on ▶. Jugalbandi and
   Mobile Vaani both show voice is what reaches the least literate users.
2. **Three door cards + "people ask" chips** on the empty screen, each with an icon a non-reader recognises
   (❓ question, 📄 contract, ⚠️ problem). The chips are real questions in the worker's language.
3. **One question per message, with tap answers** (A2J Author's "very simple" rule). Show progress as dots
   ("3 of 6 questions") so the worker knows it ends.
4. **Facts card before the check**: "Here is what I understood" with ✎ on each line. This is the moment of trust.
5. **Answer shape:** 1 headline sentence → 2–3 plain sentences → article chip → "What can I do?" chip. Long text only behind "Tell me more".
6. **Always-visible help**: ☎ 80084 and "MOHRE on WhatsApp" in the top bar (verify the number first).
7. **Safety card** for danger words, before anything else (CHAT_PLAN flag 7).
8. **Resume + delete**: "Continue where you left off?" and a visible "Delete my chat".

**Should have (C4–C6)**

9. **Contract X-ray**: a photo of the contract → a card with ✓/⚠ per term (wage, hours, leave, notice, probation),
   each ⚠ tappable to its article. Add "Things to check that aren't in your contract" (passport kept? fees paid?).
10. **"Documents to keep" checklist** (from Just Good Work): payslips, bank SMS, contract photo, attendance, messages
    from the supervisor. Shown when a case starts, because evidence is what a MOHRE claim lives on.
11. **Share to WhatsApp** for any answer card or the case summary, with no personal data in it.
12. **Helper mode** (from Haqdarshak): "I'm helping someone" switch; copy says "the worker"; a one-page printable summary.
13. **Know-your-rights library**: 10–15 short audio + card explainers tied to the Law Pack topics, cached for offline.

**Later (v2)**

14. WhatsApp channel (PRD F10) and a phone/IVR channel (Mobile Vaani model).
15. Follow-up reminders ("It's been 14 days since your employer's deadline. Have you filed?"), which need a contact
    method we currently don't store.
16. Community-level insight for NGOs (anonymous counts by issue and emirate), never per-employer.

**Small details that matter on cheap phones**

- Western digits everywhere for money and dates (already the PDF rule, CHANGES.md 23).
- Chips wrap onto two lines rather than scroll sideways; ≥ 44 px targets.
- Keep the composer above the keyboard on iOS and Android (`visualViewport`), a classic chat bug.
- A visible "Haqqi is thinking…" with the stage name; never a silent spinner over 3 s.
- Voice greeting **off by default** (privacy in shared rooms); ▶ is one tap away.
- Vibration/sound off; data use shown in the footer is overkill: just keep the page small.

## Part 3 — How to research it ourselves

**A. Desk teardown (2–3 hours, you or me).** Install and walk through: MOHRE app + its WhatsApp channel, Just Good
Work, Shuvayatra, and one general AI chat (ChatGPT/Gemini voice) in Hindi or Urdu. For each, note on one sheet:
first screen, how it asks for facts, how it shows trust (sources, disclaimers), voice support, where it dead-ends,
how long to a first useful answer. Screenshot the best and worst moment of each into `docs/research/teardown/`.

**B. Talk to people (5 conversations, as the PRD already plans, 15 minutes each).** Add to the PRD questions:
- "Show me how you'd ask a friend about this on your phone." (Watch: voice note or text? Which app?)
- "What was the last thing you asked someone about work?" (Real question bank for the chips.)
- "Would you photograph your contract for an app? What would worry you?" (Decides C4's effort.)
- For helpers: "What do you write down when a worker comes to you?" (Shapes helper mode and the facts card.)

**C. Test the C0 prototype (the most valuable step).** 5 users, 3 tasks each: ask a question, check a late-salary case,
understand a contract line. Measure time to first useful answer, taps, where they hesitate, voice vs typing, and
"would you trust this?" (1–5). Copy the Prabodhini method: same task once in the chat and once in the current form flow.
Five users find most of the big usability problems; fix, then test 5 more.

**D. Expert review.** One UAE labour lawyer or legal-aid volunteer scores 20 Ask answers with the Stanford rubric, and
one Arabic reader keeps doing the complaint review (5.6). This is the DoNotPay lesson: test quality before claiming it.

**E. During the pilot.** Counts only (door, voice use, completion, 👍/👎), plus a 1-minute voice-note interview
offer at the end ("Tell us what was hard"), stored only with consent.

## Proposed additions to CHAT_PLAN.md (for your approval)

- C0: add the teardown (A) and the two-interface test (C).
- C2: top-bar "MOHRE on WhatsApp" link, after the number is verified on mohre.gov.ae.
- C3: "Documents to keep" card when a case starts; progress dots in slot-filling.
- C7: score Ask answers with the Stanford rubric, plus an expert review of 20 answers.
- C8: helper mode moves from optional to should-have if B shows most workers come through helpers.

## Sources

- MOHRE WhatsApp: [CIPD (2017 launch)](https://www.cipd.org/en/about/news-archive/labour-disputes-uae/), [Gulf News video-call service](https://gulfnews.com/living-in-uae/ask-us/how-to-file-labour-complaints-faster-with-mohres-new-video-call-service-1.1719413316956), [Gulf News: filing a complaint](https://gulfnews.com/gulfnews/living-in-uae/ask-us/uae-how-to-file-a-labour-complaint-in-the-uae-1.1668438583728)
- Jugalbandi: [Microsoft News India](https://news.microsoft.com/en-in/features/with-help-from-next-generation-ai-indian-villagers-gain-easier-access-to-government-services/), [Thoughtworks](https://www.thoughtworks.com/clients/jugalbandi)
- Form vs conversational study: [ACL Anthology, HCI+NLP 2025](https://preview.aclanthology.org/setup/2025.hcinlp-1.6) (listing; the full page didn't load for me)
- Haqdarshak: [Our offerings](https://haqdarshak.com/our_offerings/), [Acumen](https://acumen.org/companies/haqdarshak/), [MIT Solve](https://solve.mit.edu/solutions/101897)
- Shuvayatra: [The Safe Migration App (PDF)](https://asiafoundation.org/wp-content/uploads/2016/08/The-Safe-Migration-App.pdf), [NextBillion](https://nextbillion.net/supporting-the-safe-journey-how-mobile-tech-is-making-migration-more-secure-and-less-costly/), [NRNA](https://nrna.org/news/Soft-Launch-of-Mobile-App)
- Golden Dreams: [Infosheet (PDF)](https://respect.international/wp-content/uploads/2020/06/Golden-Dreams-Infosheet.pdf), [US DOL](https://www.dol.gov/index.php/agencies/ilab/sourcingstrong/steps-to-a-social-compliance-system/step-5-monitor-compliance/technology-based-feedback-mechanisms), [MIT Solve](https://solve.mit.edu/solutions/91793)
- Just Good Work: [ETI: new interface for all literacy levels](https://www.ethicaltrade.org/resources/blog/just-good-work-app-develops-new-interface-workers-all-literacy-levels), [The Edge Malaysia](https://theedgemalaysia.com/node/659516)
- Mobile Vaani: [GSMA case study (PDF)](https://www.gsma.com/mobilefordevelopment/wp-content/uploads/2016/08/OnionDevs-Mobile-Vaani-Case-Study.pdf), [arXiv 2104.07901](https://arxiv.org/pdf/2104.07901)
- Ulula: [MIT Solve](https://solve.mit.edu/solutions/7707), [BHRRC: "kabuki theatre?"](https://www.business-humanrights.org/zh-hans/博客/is-worker-voice-technology-more-than-just-kabuki-theatre-in-the-struggle-for-labour-rights)
- A2J Author: [Chicago-Kent](https://www.kentlaw.iit.edu/institutes-centers/center-for-access-to-justice-and-technology/a2j-author), [CALI](https://www.cali.org/content/a2j-author)
- Stanford Legal Design Lab: [User research](https://justiceinnovation.law.stanford.edu/projects/ai-access-to-justice/users), [Quality rubric](https://justiceinnovation.law.stanford.edu/measuring-what-matters-a-quality-rubric-for-legal-ai-answers)
- DoNotPay: [FTC](https://www.ftc.gov/node/87474)
- Low-literacy audio consent: [arXiv 2601.17025](https://arxiv.org/pdf/2601.17025)
