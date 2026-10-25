# Haqqi pitch demo on Lovable

For the Sheraa ideathon. **25 Oct: the demo is built in this repo at `/demo` (`frontend/components/demo/`); this prompt
pack is kept in case you want a Lovable version too.** Lovable builds the screens; the answers come from the real Haqqi backend on Render
(`POST /v1/demo/ask` for questions, the normal `/v1/cases` endpoints for a case). The Gemini key stays on Render.

## How to use this

1. **Deploy the backend first.** Merge this branch so Render redeploys, then check it:
   ```bash
   curl -s https://haqqi-api.onrender.com/healthz
   curl -s -X POST https://haqqi-api.onrender.com/v1/demo/ask -H 'Content-Type: application/json' \
     -d '{"language":"en","question":"Can my company keep my passport?"}'
   ```
   The second call should return `"kind":"answer"` with an Art. 13(2) citation. (Render's free plan sleeps; the
   first call can take about a minute.)
2. **Create a new Lovable project** and paste **Prompt 1** as the first message. Paste **Prompt 2** once the first
   build is done, then **Prompt 3** for polish. Three messages keeps you inside the free plan's daily limit.
3. **Let the backend accept calls from Lovable.** In Render → haqqi-api → Environment, set `CORS_ORIGIN_REGEX` to
   your project's domains. While building, this works for the editor preview and the published app:
   `https://[a-z0-9-]+\.(lovable\.app|lovableproject\.com)`
   Once you know the published URL, narrow it, e.g. `https://haqqi-demo\.lovable\.app|https://[a-z0-9-]*<project-id>[a-z0-9-]*\.lovableproject\.com`.
   (The broad pattern lets any Lovable app call the API from a browser; per-IP rate limits still apply.)
4. **Pitch day:** see the checklist at the end.

---

## Prompt 1 — the app (paste as the first message)

````text
Build "Haqqi" (حقّي, "my right"), a mobile-first web app prototype for an ideathon pitch. It is a voice-first chat
that helps low-wage migrant workers in the UAE understand their labour rights, check what they are owed, and get a
formal Arabic complaint. This is a FRONTEND-ONLY app: do not add Supabase, Lovable Cloud, authentication, a database
or any AI integration. All answers come from an existing backend API described below. Never invent legal content
or money amounts in the frontend; show only what the API (or the fallback data file from my next message) returns.

USERS AND PRINCIPLES
- A worker on a cheap phone, often tired, sometimes with limited reading, in Hindi, Urdu, English and other languages.
- Voice first, text always. One question at a time with tap answers (chips). Short messages. Cards, not paragraphs.
- Never a dead end: every reply ends with something to tap. MOHRE help (80084) is always one tap away.
- Calm and trustworthy, not legal grey. Every legal statement shows the article it comes from.

DESIGN SYSTEM
- Colours (CSS variables, light): --primary #0F5C5A (deep teal), --primary-soft #E3F0EE, --bg #F7F2EA (warm sand),
  --card #FFFFFF, --ink #1B2626, --muted #5E6B6A, --border #E5DDD0, --warning-bg #FFF4D6, --warning-ink #7A5300,
  --danger #B42318, --danger-bg #FDECEA, --success #1E7B4C, --success-bg #E6F4EC.
  Dark mode (prefers-color-scheme): --bg #0F1716, --card #172221, --ink #EEF3F2, --muted #A3B1AF, --border #263533,
  --primary #4FB3A9, --primary-soft #18302E; keep warning/danger/success readable.
- Fonts (Google Fonts): Inter for Latin; Noto Sans Devanagari for Hindi; Noto Nastaliq Urdu for Urdu (line-height 2);
  Noto Naskh Arabic for Arabic. Base size 17px, line-height 1.55. Headlines 22px semibold.
- Radius 16px on cards, 999px on chips and buttons. Every tap target at least 48px tall. Soft shadows only.
- Icons: lucide-react. Western digits (0-9) everywhere, also in Arabic and Urdu.
- Layout: mobile-first at 375px with 16px side padding, no horizontal scroll. On screens >= 1024px wide, show the app
  inside a centred phone frame (390x844, rounded 44px, subtle shadow) on a sand background, with the Haqqi logo and
  the tagline "Your rights at work, in your language" to the left of the phone. This is the projector view.
- Logo: the wordmark "Haqqi" plus "حقّي" in Noto Naskh Arabic, teal.

LANGUAGES
- Language picker offers: English, हिन्दी, اردو, മലയാളം, বাংলা, Tagalog, नेपाली, العربية (each with a flag).
- Full UI strings in English, Hindi and Urdu (table below). For Malayalam, Bengali, Tagalog, Nepali and Arabic, use the
  English UI strings with a small "Demo in English" tag, but still send that language code to the API so answers come
  back in that language.
- Urdu and Arabic switch the whole app to dir="rtl" (mirror layouts, chips, icons with direction).
- Store the chosen language in localStorage (wrap in try/catch).

UI STRINGS (en | hi | ur)
greeting: "Hi, I'm Haqqi. I help workers in the UAE understand their rights at work." | "नमस्ते, मैं हक़्क़ी हूँ। मैं UAE में काम करने वालों को उनके अधिकार समझने में मदद करता हूँ।" | "السلام علیکم، میں حقی ہوں۔ میں UAE میں کام کرنے والوں کو ان کے حقوق سمجھنے میں مدد کرتا ہوں۔"
placeholder: "Tell me what happened, or ask a question" | "बताइए क्या हुआ, या कोई सवाल पूछिए" | "بتائیں کیا ہوا، یا کوئی سوال پوچھیں"
doorAsk: "I have a question" | "मेरा एक सवाल है" | "میرا ایک سوال ہے"
doorContract: "Explain my contract" | "मेरा कॉन्ट्रैक्ट समझाइए" | "میرا معاہدہ سمجھائیں"
doorProblem: "Something went wrong at work" | "काम पर कुछ गलत हुआ" | "کام پر کچھ غلط ہوا"
peopleAsk: "People often ask" | "लोग अक्सर पूछते हैं" | "لوگ اکثر پوچھتے ہیں"
listening: "Listening…" | "सुन रहा हूँ…" | "سن رہا ہوں…"
listen: "Listen" | "सुनिए" | "سنیں"
checkCase: "Check my situation" | "मेरी स्थिति जाँचिए" | "میری صورتحال چیک کریں"
notSure: "Not sure" | "पता नहीं" | "معلوم نہیں"
unsure: "I'm not sure about this one. MOHRE can help: call 80084 or message them on WhatsApp." | "इस बारे में मुझे पक्का नहीं पता। MOHRE मदद कर सकता है: 80084 पर कॉल करें या WhatsApp पर मैसेज करें।" | "اس بارے میں مجھے یقین نہیں۔ MOHRE مدد کر سکتا ہے: 80084 پر کال کریں یا WhatsApp پر پیغام بھیجیں۔"
offTopic: "I can only help with work and labour rights in the UAE." | "मैं सिर्फ़ UAE में काम और मज़दूर अधिकारों में मदद कर सकता हूँ।" | "میں صرف UAE میں کام اور مزدوروں کے حقوق میں مدد کر سکتا ہوں۔"
privacy: "Please don't include your name, phone, passport or ID numbers." | "कृपया अपना नाम, फ़ोन, पासपोर्ट या ID नंबर न लिखें।" | "براہ کرم اپنا نام، فون، پاسپورٹ یا ID نمبر نہ لکھیں۔"
understood: "Here is what I understood" | "मैंने यह समझा" | "میں نے یہ سمجھا"
confirm: "Yes, check my case" | "हाँ, मेरा केस जाँचिए" | "ہاں، میرا کیس چیک کریں"
deleteChat: "Delete my chat" | "मेरी चैट मिटाएँ" | "میری چیٹ مٹائیں"
danger: "Are you in danger? Get help now." | "क्या आप खतरे में हैं? अभी मदद लें।" | "کیا آپ خطرے میں ہیں؟ ابھی مدد لیں۔"
disclaimer: "Legal information, not legal advice. MOHRE decides. Call 80084." | "यह कानूनी जानकारी है, कानूनी सलाह नहीं। फ़ैसला MOHRE करता है। 80084 पर कॉल करें।" | "یہ قانونی معلومات ہیں، قانونی مشورہ نہیں۔ فیصلہ MOHRE کرتا ہے۔ 80084 پر کال کریں۔"
For any other string you need, write English and add Hindi and Urdu drafts.

SCREENS AND BEHAVIOUR
1. Language picker (first visit): 8 large rows, flag + native name. Tap → chat home.

2. Chat home (one screen that becomes the conversation):
   - Top bar: logo left; right: language switch (flag), a phone icon that opens tel:80084, a WhatsApp icon that opens
     https://wa.me/971600590000 (MOHRE WhatsApp), and a "⋯" menu with "Delete my chat", "Large text" toggle and
     "I'm helping someone" toggle (helper mode changes "you/your" copy to "the worker" in the UI chrome only).
   - Empty state: Haqqi avatar bubble with the greeting and a ▶ Listen button; then three big "door" cards with
     icons (HelpCircle "doorAsk", FileText "doorContract", AlertTriangle "doorProblem"); then "peopleAsk" with
     horizontally wrapping chips of starter questions (from the fallback file, in the current language if present,
     else English).
   - Composer pinned to the bottom, above the keyboard on iOS and Android (use visualViewport): a camera button
     (opens the contract flow), a text field with the placeholder, and a big round teal mic button (56px).
   - Above the composer, one small muted line: the disclaimer.
   - Tapping a starter chip sends it as the worker's message. Tapping doorAsk focuses the input; doorContract opens
     the contract flow; doorProblem sends the worker into the case flow (screen 4) and Haqqi replies
     "Tell me what happened, in your own words. You can speak or type." with the privacy line under it.

3. Ask (any free text the worker sends that is not in the case flow):
   - Show the worker's bubble, then a typing bubble with a stage label ("Searching the law…").
   - Call POST /v1/demo/ask. Render the reply as a Haqqi card:
     kind "answer": bold headline, then the answer text, then one chip per citation (e.g. "Art. 13(2)"; derive the
     short label from ref_en before the comma). Tapping a chip opens a bottom sheet with ref_en, title, text_en and
     text_ar (Arabic in Noto Naskh, dir="rtl"). Under the card: ▶ Listen, "Share on WhatsApp"
     (https://wa.me/?text= headline + answer + ref labels, no personal data).
     If suggest_case is true, add an offer card: "It sounds like this may be happening to you. Want me to check your
     situation and what you may be owed?" with buttons [checkCase] [Not now]. checkCase starts the case flow and uses
     the worker's message as the start of their story.
     kind "unsure": the "unsure" string plus the contact buttons. kind "off_topic": the "offTopic" string plus the
     three door cards again.
   - If safety is true: BEFORE the answer, show a red emergency card (danger-bg) titled with the "danger" string and
     one big call button per contact in `contacts` (999 police, 800 7283 human trafficking hotline first), then MOHRE.
     Also show it, without calling the API first, when the worker's text contains words like beat, hit me, locked,
     no food, no water, trafficking, forced, sexual, kill (English only).

4. Case flow ("Something went wrong"):
   a. Voice or text story. Mic: tap to start, tap to stop, 2-minute limit. While recording, the composer turns into
      a full-width recording bar with a pulsing red dot, the "listening" string and a timer, so it is obvious the app
      is listening. Send the audio to POST /v1/transcribe, then show the transcript in the worker's bubble with a small
      "✎ Fix" link that puts the text back in the input. If the mic is blocked or unsupported, say so and suggest typing.
   b. Call POST /v1/cases with {language, story}. Show stage "Reading your story…".
   c. If status is "out_of_scope": show a referral card with the `referral` text and the contact buttons. Stop.
   d. Ask ONLY for what is still missing, one question per Haqqi message, with chips and a "notSure" chip, and a row
      of progress dots ("2 of 4"). Use the extracted values for everything else. Questions and chips:
      - emirate: "Which emirate do you work in?" chips: Abu Dhabi, Dubai, Sharjah, Ajman, Umm Al Quwain,
        Ras Al Khaimah, Fujairah → values abu_dhabi, dubai, sharjah, ajman, umm_al_quwain, ras_al_khaimah, fujairah.
      - zone: "Is your company in a free zone (like JAFZA or DMCC), or not?" chips: "Not in a free zone" → mainland,
        "Free zone" → free_zone, "DIFC" → difc, "ADGM" → adgm. notSure → explain "Look at your visa or labour card:
        a free zone name appears there" and ask again.
      - worker_type: "Who do you work for?" chips: "A company" → private_sector, "A family, at their home" → domestic.
      - termination: "Are you still working there?" chips: "Yes, still working" → still_employed,
        "They ended my job" → employer, "I resigned" → resigned.
      - start_date / end_date: "When did you start?" / "What was your last day?" chips: month + year pickers
        (last 10 years), then an optional "Exact day" number pad; send YYYY-MM-DD (day 1 if no exact day).
      - total_wage_aed / basic_wage_aed: "What is your total monthly salary?" / "And your basic salary (on your
        contract)?" a numeric keypad (inputmode="numeric"), digits only.
      Ask in this order, skipping known fields: zone, worker_type, emirate, termination, start_date, end_date (only if
      the job ended), total_wage_aed, basic_wage_aed. A free-text answer to a chip question is fine: keep it as a note,
      but still ask for the value with chips.
   e. Facts card ("understood"): one row per fact (emirate, company type, zone, started, last day, total salary,
      basic salary, what happened, notice days in contract, notice days given) with ✎ on each row to change it
      (opens the same chip question). Button [confirm].
   f. PATCH /v1/cases/{id} with ONLY the fields the worker answered or changed (never send null for a field: the API
      keeps the extracted values for anything you leave out). If status comes back "out_of_scope", show the referral.
      On 422 show "Some details don't fit together. Please check the dates and salary." and reopen the facts card.
   g. POST /v1/cases/{id}/analyze (Server-Sent Events). Show a progress message that ticks through the stages as they
      arrive: retrieving "Searching the law", calculating "Calculating what you're owed", analysing "Checking your
      rights", critiquing "Double-checking", revising "Fixing a detail", writing "Writing in your language".
   h. On "done", render the Analysis as cards in the chat:
      - Verdict card: writer.headline (or "Here is what I found"), writer.explanation paragraphs.
        If analysis.unsure: a warning card "Haqqi isn't sure about your case" + contacts, title the findings
        "Possible issues", and do not show the complaint card.
      - Findings card: one row per violation: issue text, a chip with the article label (from law_id/article_no/
        clause_no: "Art. 43(3)"; cr1-2022 → "CR Art. 27(1)") that opens the quote in the bottom sheet, and a confidence
        pill (high/medium/low). Label the card "Shown in English".
      - Claim card: one row per claim line: item, amount "AED 3,000.00" (amount_aed is a decimal string; format with
        thousands separators and 2 decimals; null → "Not calculated" with the note), the formula in small muted text,
        and the plain-language line from writer.amount_lines[i] when the lengths match. A bold total row (total_aed).
        Under it: "Every amount comes from a calculator, not from AI."
        If worker_owes is not empty, a separate amber card "You may owe your employer" with those lines.
        If above_mohre_limit, a note "Above AED 50,000: MOHRE refers this to court."
      - Next steps card: numbered list from writer.checklist (or next_steps). Add a fixed first step when the worker
        is still employed and wages are unpaid: "MOHRE has a confidential salary complaint: your employer is not told
        who complained. Use the MOHRE app or call 80084." Then "Documents to keep" from documents_to_gather as a
        checklist with checkboxes (local state only).
      - Complaint card: "Your complaint in Arabic, ready for MOHRE" with a thumbnail-style preview (Arabic text block
        from writer.letter_facts_ar, RTL) and optional fields name, labour card number, employer (with the note
        "Printed in the letter only. Never stored."). Button "Get my complaint (PDF)" → POST /v1/cases/{id}/complaint
        with only the filled fields → PDF blob → on phones use navigator.share({files}) if available ("Save or share
        PDF"), else open the blob URL; on desktop download "haqqi-complaint.pdf".
      - "Share summary on WhatsApp" (headline + total + "Checked with Haqqi"), no personal data.
   i. "error" event or failure: "The assistant is busy. Please try again." + Retry + contacts, and offer
      "See an example case" which renders the fallback example result.

5. Contract X-ray (camera button or doorContract):
   - Sheet: "Take a photo of each page of your contract. Cover your passport number and Emirates ID first, or I will
     hide them." [Take photo] [Paste text] [Use a sample contract].
   - This flow is a scripted demo: whatever the worker picks, show a scanning animation (a light bar moving over a
     blurred page, 2.5 s, "Reading your contract…"), then the X-ray card from the fallback file: one row per term with
     ✓ (success) or ⚠ (warning), the term in plain words, and a law chip (opens the sheet with the official text).
     Then "Use these details to check my case" → case flow: the worker still tells their story, and the contract's
     values (CONTRACT_PREFILL in the fallback file) count as answers already given: skip those questions, show them on
     the facts card, and include them in the PATCH.
   - Small muted note on the card: "Demo: sample contract".

6. Listen (▶): window.speechSynthesis with lang en-US / hi-IN / ur-PK / ar-AE / ml-IN / bn-BD / fil-PH / ne-NP.
   Show the button only if speechSynthesis.getVoices() has a voice for that language (check again on voiceschanged).
   Never play audio automatically. While speaking, the button becomes ■ Stop.

7. Returning visitor: if localStorage has an earlier conversation (messages only, no audio), show "Continue your
   chat?" [Continue] [Start new]. "Delete my chat" clears it immediately and confirms "Deleted".

8. Large text toggle: base size 20px. Respect prefers-reduced-motion.

API (existing backend; base URL constant API_BASE = "https://haqqi-api.onrender.com"; JSON unless noted)
- GET /healthz → {status:"ok", db:"ok"|"down", version}. Call it once when the app opens to wake the server
  (it can take ~60 s after idle). While it hasn't answered, show a small "Waking up Haqqi…" pill in the top bar.
- POST /v1/demo/ask  body {language, question}  (question 1–1000 chars; language one of en,hi,ur,ml,bn,tl,ne,ar)
  → {kind:"answer"|"unsure"|"off_topic", headline, answer, citations:[{chunk_id, ref_en, ref_ar, title, text_en,
     text_ar}], suggest_case:boolean, safety:boolean, contacts:[{label, number}]}
- POST /v1/transcribe  multipart form: audio (Blob from MediaRecorder; file name recording.webm or recording.m4a),
  language → {text, detected_language}. Max 3 MB. Do not set Content-Type yourself.
  MediaRecorder: prefer "audio/webm;codecs=opus", else "audio/mp4" (iPhone Safari).
- POST /v1/cases  body {language, story} (story 1–8000 chars) → CaseView:
  {id, status:"out_of_scope"|"need_info"|"ready"|"confirmed"|"analysed", extracted:{emirate, zone, worker_type,
   contract_type, start_date, end_date, basic_wage_aed, total_wage_aed, months_unpaid, termination,
   notice_days_contract, notice_days_given, unused_leave_days, issue_types:[...], facts_summary_en, ...(all nullable)},
   missing:[...], missing_fields:[...], referral:string|null, referral_kind:"domestic"|"difc_adgm"|"free_zone"|null,
   confirmed, analysis}
- PATCH /v1/cases/{id}  body: only the fields you have values for, e.g. {"zone":"mainland","worker_type":
  "private_sector","emirate":"abu_dhabi","termination":"employer","end_date":"2026-09-20","basic_wage_aed":"2000",
  "total_wage_aed":"3000"} → CaseView. Rules the API checks: basic ≤ total; end_date required unless
  termination is still_employed, and empty if still employed; end_date not before start_date.
- POST /v1/cases/{id}/analyze  (no body) → text/event-stream. Read it with fetch + response.body.getReader() and a
  TextDecoder; events are separated by a blank line, each "event: <name>\ndata: <json>". Names: retrieving,
  calculating, analysing, critiquing, revising, writing (data {}), then done (data = Analysis) or error
  (data {detail}). Do not use EventSource (it cannot POST).
  Analysis: {in_scope, referral, violations:[{issue, article:{chunk_id, law_id, article_no, clause_no, quote},
  confidence}], not_covered:[...], claim:[{item, amount_aed:string|null, formula, article, note}], worker_owes:[same],
  total_aed:string, above_mohre_limit, next_steps:[...], documents_to_gather:[...], time_limit_note, unsure:boolean,
  writer:{headline, explanation, amount_lines:[...], checklist:[...], letter_facts_ar, letter_facts_translation}|null,
  writer_failed:boolean}
- POST /v1/cases/{id}/complaint  body {name?, labour_card?, employer?} → application/pdf.
- Errors: FastAPI {detail}. 429 = "Too many requests. Please wait a few minutes." 502/503 = busy. Treat any request
  that takes longer than 45 s (90 s for analyze) as failed.

DEMO MODE (fallback; the demo must never die on stage)
- If /healthz has not answered within 45 s, or a call fails, switch that step to the fallback data (next message
  will give you src/data/fallback.ts): Ask → match the question to the closest prepared answer by keywords (passport,
  salary/late/paid, fee/visa cost, overtime, probation, notice/resign, gratuity/end of service, sick, change job/
  transfer, contract language), else show "unsure"; Case → the example Ayesha result.
- Show a small grey "Demo mode" pill in the top bar while fallback is used.
- Presenter controls (only with ?presenter=1 in the URL): tap the logo 5 times to toggle forced demo mode; key R
  resets the conversation; key 1 sends the passport starter question; key 2 sends the Ayesha story; key 3 opens the
  contract X-ray; key 4 sends the danger example "My supervisor beats us and locked us in the room".

Do not show any number, article or legal statement that isn't from the API or the fallback file.
````

---

## Prompt 2 — fallback data (paste after the first build)

````text
Create src/data/fallback.ts with exactly this content (keep the texts as they are; they come from the official law
text and from the backend's calculator), and wire it into demo mode, the starter chips, the example case and the
contract X-ray as described before.

export const STARTERS = {
  en: ["My salary is late", "Can my company keep my passport?", "I paid money to get this job",
       "How much overtime pay should I get?", "How long can probation be?", "How much notice must I give?",
       "How is gratuity worked out?", "I was sick. Do I still get paid?", "Can I change my company?",
       "My contract is not in my language"],
  hi: ["मेरी तनख़्वाह देर से आ रही है", "क्या कंपनी मेरा पासपोर्ट रख सकती है?", "मैंने यह नौकरी पाने के लिए पैसे दिए",
       "ओवरटाइम का कितना पैसा मिलना चाहिए?", "प्रोबेशन कितना लंबा हो सकता है?", "मुझे कितना नोटिस देना होगा?"],
  ur: ["میری تنخواہ دیر سے آ رہی ہے", "کیا کمپنی میرا پاسپورٹ رکھ سکتی ہے؟", "میں نے یہ نوکری لینے کے لیے پیسے دیے",
       "اوور ٹائم کا کتنا پیسہ ملنا چاہیے؟", "پروبیشن کتنا لمبا ہو سکتا ہے؟", "مجھے کتنا نوٹس دینا ہوگا؟"],
};

const FDL = "Federal Decree-Law No. 33 of 2021";
const CR = "Cabinet Resolution No. 1 of 2022";

export const ANSWERS = [
  { keys: ["salary", "late", "paid", "wage", "pay"], suggest_case: true,
    headline: "Your employer must pay your salary on time.",
    answer: "The law says wages must be paid on their due dates, through the system MOHRE approves. If your pay is late, you can report it to MOHRE. MOHRE also has a confidential salary complaint, so your employer is not told who complained.",
    citations: [
      { ref_en: `Art. 22(2), ${FDL}`, text_en: "The Employer is obligated to pay the wages to his Workers on their due dates in accordance with the systems approved in the Ministry and the conditions, controls and procedures specified in the Executive Regulation of this Decree by law." },
      { ref_en: `Art. 16(1), ${CR}`, text_en: "The employer shall commit to pay his workers' wages on due dates and in accordance with the following conditions, controls, and procedures: a. The wages shall be paid on due dates…" } ] },
  { keys: ["passport", "documents", "id card"], suggest_case: true,
    headline: "No. Your company cannot keep your passport.",
    answer: "The law says your employer must not keep your official documents. Ask for your passport back, in writing if you can. If they refuse, call MOHRE on 80084.",
    citations: [ { ref_en: `Art. 13(2), ${FDL}`, text_en: "The Employer must: Not withhold the official documents of the Worker or force him to leave the State upon the end of the labour relation." } ] },
  { keys: ["fee", "fees", "recruitment", "visa cost", "agent", "money to get"], suggest_case: true,
    headline: "No. Your employer cannot make you pay for your recruitment.",
    answer: "The law forbids charging workers the costs of recruitment and employment, directly or indirectly, for example by cutting your salary. Keep any receipts or messages and tell MOHRE.",
    citations: [ { ref_en: `Art. 6(4), ${FDL}`, text_en: "The Employer is prohibited from charging the Worker the fees and costs of recruitment and employment or collecting them from him, whether directly or indirectly." } ] },
  { keys: ["overtime", "extra hours", "hours"], suggest_case: false,
    headline: "Overtime is paid at your basic hourly pay plus at least 25%.",
    answer: "Normal hours are at most 8 a day or 48 a week. Extra hours should be no more than 2 a day, and are paid at your basic hourly pay plus at least 25%. Overtime between 10 pm and 4 am is plus at least 50% (shift workers excluded).",
    citations: [
      { ref_en: `Art. 17(1), ${FDL}`, text_en: "The maximum normal working hours for Workers shall be eight (8) hours per day or forty-eight (48) hours per week." },
      { ref_en: `Art. 19(2), ${FDL}`, text_en: "If circumstances of work require that the Worker works for more than the normal working hours, the extra time shall be considered overtime, for which the Worker shall receive a wage equal to that corresponding to his normal working hours - calculated according to the basic wage - plus an increase of at least twenty-five percent (25%) of such wage." } ] },
  { keys: ["probation", "trial"], suggest_case: false,
    headline: "Probation can be at most 6 months.",
    answer: "Your employer can put you on probation for up to 6 months from your first day. To end your job during probation, they must tell you in writing at least 14 days before.",
    citations: [ { ref_en: `Art. 9(1), ${FDL}`, text_en: "The Employer may appoint the Worker under the Probation Period for a period not exceeding six (6) months as of the date of commencing work, and he may terminate the Worker's service during this period after notifying the Worker in writing at least fourteen (14) days prior to the date specified for termination of service." } ] },
  { keys: ["notice", "resign", "quit", "leave my job", "fired"], suggest_case: true,
    headline: "Notice is what your contract says: at least 30 days, at most 90.",
    answer: "Either side can end the contract with written notice. If one side does not give the notice, it must pay the other side the wage for the notice period, or the part that was missed.",
    citations: [
      { ref_en: `Art. 43(1), ${FDL}`, text_en: "Either party to the employment contract may terminate the contract for any legitimate reason, provided that the other party is notified in writing, and commits to work within the warning period agreed upon in the contract, provided that the period is not less than thirty (30) days and not more than ninety (90) days." },
      { ref_en: `Art. 43(3), ${FDL}`, text_en: "The party who does not abide by the warning period must pay the other party a compensation called a warning allowance, even if the failure to warn does not result in harm to the other party. Such compensation shall be equal to the Worker's wage for the entire warning period or the remaining part of it." } ] },
  { keys: ["gratuity", "end of service", "eos"], suggest_case: true,
    headline: "After 1 year, you get gratuity based on your basic pay.",
    answer: "For each of your first 5 years: 21 days of basic pay. For each year after that: 30 days. The total cannot be more than 2 years' pay. Tell me your dates and salary and I can work it out for you.",
    citations: [
      { ref_en: `Art. 51(2), ${FDL}`, text_en: "The foreign full-time Worker, who has completed one or more years of continuous service, is entitled to an end-of-service gratuity upon the end of his service, calculated according to the basic wage, as follows: a. The wage of twenty-one (21) days for each year of the first five years of service. b. The wage of thirty (30) days for each year in excess of that." },
      { ref_en: `Art. 51(6), ${FDL}`, text_en: "The foregoing is provided that the total end-of-service gratuity for the foreign Worker does not exceed two years' wage." } ] },
  { keys: ["sick", "ill", "hospital", "medical"], suggest_case: false,
    headline: "After probation, you can get up to 90 days of sick leave a year.",
    answer: "Tell your employer within 3 working days and give a medical report. The first 15 days are on full pay, the next 30 days on half pay, and the rest unpaid. During probation, sick leave is unpaid.",
    citations: [
      { ref_en: `Art. 31(1), ${FDL}`, text_en: "If the Worker suffers an illness that is not caused by a work injury, he must inform the Employer or his representative of his illness, within a period not exceeding three (3) business days and submit a medical report on his condition issued by the Medical Authority." },
      { ref_en: `Art. 31(3), ${FDL}`, text_en: "After the Probation Period, the Worker may receive a sick leave of no more than (90) ninety consecutive or intermittent days per year, provided that it shall be calculated as follows: a. The first fifteen (15) days with full pay. b. The following thirty (30) days with half pay. c. The following period shall be unpaid." } ] },
  { keys: ["change", "transfer", "new company", "new job", "move"], suggest_case: false,
    headline: "In many cases, yes: for example when your contract ends.",
    answer: "You can move to another employer when your contract ends without being renewed, or when it is ended in the ways the law allows. MOHRE can tell you exactly what applies to you.",
    citations: [ { ref_en: `Art. 27(1), ${CR}`, text_en: "The worker may, upon expiry of his employment contract in accordance with the provisions of the Federal Decree-Law, transfer to work for another employer in accordance with the following conditions and situations: a. If the contract's term, agreed upon between the parties, has expired without being renewed. b. If the contract is termination while still in force in accordance with what is stipulated in Articles (42) and (45) of the Federal Decree-Law." } ] },
  { keys: ["contract", "language", "copy", "arabic"], suggest_case: false,
    headline: "Your contract must be in Arabic and in a language you understand.",
    answer: "Your employer must give you your own copy of the contract. It must be in Arabic, plus another language you understand, and both must say the same thing.",
    citations: [
      { ref_en: `Art. 8(1), ${FDL}`, text_en: "The Employer must conclude an employment contract with the Worker, according to the form of work agreed upon, provided that the contract is in two copies, one of which shall be kept by the Employer and the other shall be handed to the Worker…" },
      { ref_en: `Art. 66(2), ${FDL}`, text_en: "The Employer is obligated to use Arabic in concluding contracts with Workers… provided that, besides Arabic, another language understood by the non-Arabic speaking Worker shall be used, and the text in the other language shall match the Arabic text, and in the event case of dispute, the Arabic text shall prevail." } ] },
];

// The pitch story (illustrative persona, not a real person). Figures are the backend calculator's output for it.
export const AYESHA_STORY = "I worked as a cashier in a supermarket in Abu Dhabi from 1 June 2024. On 20 September my manager told me my job ends today. They gave me no notice. My contract says 30 days' notice. My basic salary is 2,000 dirhams and my total salary is 3,000.";

export const EXAMPLE_FACTS = { emirate: "Abu Dhabi", worker: "A company", zone: "Not in a free zone",
  started: "1 June 2024", lastDay: "20 September 2026", total: "AED 3,000", basic: "AED 2,000",
  happened: "They ended my job", noticeContract: "30 days", noticeGiven: "0 days" };

export const EXAMPLE_RESULT = {
  headline: "You were let go without notice. You are owed notice pay and gratuity.",
  explanation: "Your employer ended your job on the same day, without the 30 days' notice in your contract. The law says they must then pay you your wage for the notice period. You worked for more than 2 years, so you are also owed end-of-service gratuity.",
  violations: [
    { issue: "The employer ended the contract without the written notice the contract requires.", ref: "Art. 43(1)", confidence: "high" },
    { issue: "Notice that was not given must be paid as a notice allowance.", ref: "Art. 43(3)", confidence: "high" },
    { issue: "More than one year of service: end-of-service gratuity is due.", ref: "Art. 51(2)", confidence: "high" },
  ],
  claim: [
    { item: "Notice pay", amount: "3,000.00", formula: "(30 days' notice − 0 days given) = 30 days × AED 100.00 daily total wage (AED 3,000.00 ÷ 30)", ref: "Art. 43(3)" },
    { item: "End-of-service gratuity", amount: "3,229.59", formula: "842 service days ÷ 365 = 2.3068 years; 2.3068 × 21 = 48.4438 days × AED 66.67 daily basic wage (AED 2,000.00 ÷ 30) = AED 3,229.59", ref: "Art. 51(2)" },
  ],
  total: "6,229.59",
  nextSteps: ["Ask your employer in writing for your notice pay and gratuity.", "If they do not pay, file a complaint with MOHRE (app, website or 80084).", "End-of-service dues must be paid within 14 days of your last day."],
  documents: ["Your contract or offer letter", "Bank statements or salary slips", "Any message about your job ending", "Your labour card or Emirates ID copy"],
  letterPreviewAr: "أعمل أمينة صندوق في متجر في أبوظبي منذ 1 يونيو 2024. في 20 سبتمبر 2026 أبلغني المدير بإنهاء عملي في اليوم نفسه دون أي إنذار، رغم أن عقدي ينص على مدة إنذار 30 يومًا.",
};

// Scripted contract X-ray (synthetic sample contract).
export const CONTRACT_XRAY = [
  { ok: true,  term: "Job: Cashier. Basic salary 2,000, total 3,000 a month.", ref: null },
  { ok: false, term: "Hours: 9 a day, 6 days a week (54 a week). The normal maximum is 8 a day or 48 a week; extra hours must be paid as overtime.", ref: "Art. 17(1)" },
  { ok: true,  term: "Probation: 6 months. That is the legal maximum.", ref: "Art. 9(1)" },
  { ok: false, term: "Notice: 120 days. The law allows 30 to 90 days.", ref: "Art. 43(1)" },
  { ok: true,  term: "Annual leave: 30 days a year.", ref: "Art. 29(1)" },
  { ok: false, term: "Visa costs are taken from your salary. Your employer cannot charge you recruitment costs.", ref: "Art. 6(4)" },
  { ok: false, term: "The company keeps your passport \"for safekeeping\". This is not allowed.", ref: "Art. 13(2)" },
  { ok: false, term: "The contract is only in English. It must be in Arabic plus a language you understand.", ref: "Art. 66(2)" },
];
export const CONTRACT_PREFILL = { emirate: "abu_dhabi", total_wage_aed: "3000", basic_wage_aed: "2000", start_date: "2024-06-01", notice_days_contract: 90 };
````

---

## Prompt 3 — polish (paste last)

````text
Polish pass, keep all behaviour:
1. Check every screen at 375px and 320px wide: no horizontal scroll, chips wrap, cards fit, composer stays above the
   keyboard on iPhone Safari and Android Chrome.
2. Check Urdu and Arabic are fully right-to-left (bubbles, chips, progress dots, icons with direction) and that
   amounts and dates stay in Western digits.
3. Add gentle motion: messages fade and rise in (150 ms), the typing bubble pulses, the stage list ticks with a check
   icon, the recording dot pulses; all off under prefers-reduced-motion.
4. On the desktop phone-frame view, add under the tagline three short lines: "Speak in your language",
   "Every answer cites the law", "Every amount from a calculator, not AI", and a QR code (generated client-side) of
   the current page URL with "Try it on your phone".
5. Make sure no request blocks the UI: every button shows a loading state, every failure shows a retry and the
   80084 button, and demo mode takes over silently when the backend is unreachable.
6. Accessibility: aria-labels on icon buttons, focus outlines, colour contrast AA in light and dark mode.
````

---

## Pitch-day checklist

- [ ] The day before: run the two curl checks above; do one full Ayesha run on the published Lovable URL on your phone.
- [ ] Keep rehearsals light on the pitch day: the free Gemini tier allows about 20 requests per model per day
      (4 models, then K2, which is slower). One full case uses 4–6 requests; each question uses 1.
- [ ] 3 minutes before you go on: open the app (it wakes Render) and ask one starter question.
- [ ] Open with `?presenter=1` so keys 1–4 and R work; tap the logo 5 times if you need demo mode.
- [ ] Judges on the venue Wi-Fi share one IP: 30 questions and 10 cases per 10 minutes in total.
- [ ] Say "AI" for the answers and "calculator" for the money; never "lawyer".
