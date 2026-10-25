/**
 * Fallback content for the pitch demo: used when the backend is asleep, out of quota or forced off by the presenter.
 * Law quotes are the official English text from data/law; the example figures are the backend calculator's output
 * for TC-02 (backend/tests/core/CASES.md). Nothing here is computed in the browser.
 */

import type { Analysis, Citation } from "@/lib/types";

import type { AskReply, LawClause } from "./logic";

const FDL = "Federal Decree-Law No. 33 of 2021";
const CR = "Cabinet Resolution No. 1 of 2022";

function clause(chunkId: string, title: string, textEn: string): LawClause {
  const [law, art, cl] = chunkId.split(":");
  const no = art.replace("art", "");
  const ref = cl ? `${no}(${cl.replace("cl", "")})` : no;
  return { chunk_id: chunkId, ref_en: `Art. ${ref}, ${law === "cr1-2022" ? CR : FDL}`, ref_ar: "", title, text_en: textEn, text_ar: "" };
}

export const LAW = {
  art6_4: clause("fdl33-2021:art6:cl4", "Recruitment and Employment of Workers", "The Employer is prohibited from charging the Worker the fees and costs of recruitment and employment or collecting them from him, whether directly or indirectly."),
  art8_1: clause("fdl33-2021:art8:cl1", "Employment Contract", "The Employer must conclude an employment contract with the Worker, according to the form of work agreed upon, provided that the contract is in two copies, one of which shall be kept by the Employer and the other shall be handed to the Worker, in accordance with the forms specified by the Executive Regulation of this Decree by law."),
  art9_1: clause("fdl33-2021:art9:cl1", "Probation Period", "The Employer may appoint the Worker under the Probation Period for a period not exceeding six (6) months as of the date of commencing work, and he may terminate the Worker's service during this period after notifying the Worker in writing at least fourteen (14) days prior to the date specified for termination of service."),
  art13_2: clause("fdl33-2021:art13:cl2", "Employer's Obligations", "The Employer must: Not withhold the official documents of the Worker or force him to leave the State upon the end of the labour relation."),
  art17_1: clause("fdl33-2021:art17:cl1", "Working Hours", "The maximum normal working hours for Workers shall be eight (8) hours per day or forty-eight (48) hours per week."),
  art19_2: clause("fdl33-2021:art19:cl2", "Overtime", "If circumstances of work require that the Worker works for more than the normal working hours, the extra time shall be considered overtime, for which the Worker shall receive a wage equal to that corresponding to his normal working hours - calculated according to the basic wage - plus an increase of at least twenty-five percent (25%) of such wage."),
  art22_2: clause("fdl33-2021:art22:cl2", "Determining the Amount or Type of Wage and Paying It", "The Employer is obligated to pay the wages to his Workers on their due dates in accordance with the systems approved in the Ministry and the conditions, controls and procedures specified in the Executive Regulation of this Decree by law."),
  art29_1: clause("fdl33-2021:art29:cl1", "Annual leave", "Without prejudice to the Worker's rights acquired for the period preceding the date of enforcement of the provisions of this Decree by law, the Worker shall be entitled to an annual leave with full pay of not less than: a. Thirty days for each year of his extended service."),
  art31_3: clause("fdl33-2021:art31:cl3", "Sick Leave", "After the Probation Period, the Worker may receive a sick leave of no more than (90) ninety consecutive or intermittent days per year, provided that it shall be calculated as follows: a. The first fifteen (15) days with full pay. b. The following thirty (30) days with half pay. c. The following period shall be unpaid."),
  art43_1: clause("fdl33-2021:art43:cl1", "Employment Contract Termination Warning", "Either party to the employment contract may terminate the contract for any legitimate reason, provided that the other party is notified in writing, and commits to work within the warning period agreed upon in the contract, provided that the period is not less than thirty (30) days and not more than ninety (90) days."),
  art43_3: clause("fdl33-2021:art43:cl3", "Employment Contract Termination Warning", "The party who does not abide by the warning period must pay the other party a compensation called a warning allowance, even if the failure to warn does not result in harm to the other party. Such compensation shall be equal to the Worker's wage for the entire warning period or the remaining part of it."),
  art51_2: clause("fdl33-2021:art51:cl2", "End-of-Service Gratuity for Full-Time Workers", "The foreign full-time Worker, who has completed one or more years of continuous service, is entitled to an end-of-service gratuity upon the end of his service, calculated according to the basic wage, as follows: a. The wage of twenty-one (21) days for each year of the first five years of service. b. The wage of thirty (30) days for each year in excess of that."),
  art51_6: clause("fdl33-2021:art51:cl6", "End-of-Service Gratuity for Full-Time Workers", "The foregoing is provided that the total end-of-service gratuity for the foreign Worker does not exceed two years' wage."),
  art66_2: clause("fdl33-2021:art66:cl2", "Adopted Language", "The Employer is obligated to use Arabic in concluding contracts with Workers, and in writing and publishing instructions and circulars that he is obligated to issue; provided that, besides Arabic, another language understood by the non-Arabic speaking Worker shall be used, and the text in the other language shall match the Arabic text, and in the event case of dispute, the Arabic text shall prevail."),
  cr27_1: clause("cr1-2022:art27:cl1", "Transfer of Workers", "The worker may, upon expiry of his employment contract in accordance with the provisions of the Federal Decree-Law, transfer to work for another employer in accordance with the following conditions and situations: a. If the contract's term, agreed upon between the parties, has expired without being renewed. b. If the contract is termination while still in force in accordance with what is stipulated in Articles (42) and (45) of the Federal Decree-Law."),
} satisfies Record<string, LawClause>;

export const MOHRE_CONTACTS = [
  { label: "MOHRE labour claims and advice", number: "80084" },
  { label: "MOHRE WhatsApp", number: "600590000" },
];
export const EMERGENCY_CONTACTS = [
  { label: "Police (emergency)", number: "999" },
  { label: "Human trafficking hotline (800 SAVE)", number: "8007283" },
];

export const STARTERS: Record<"en" | "hi" | "ur" | "ar", string[]> = {
  en: [
    "My salary is late",
    "Can my company keep my passport?",
    "I paid money to get this job",
    "How much overtime pay should I get?",
    "How long can probation be?",
    "How much notice must I give?",
    "How is gratuity worked out?",
    "I was sick. Do I still get paid?",
  ],
  hi: [
    "मेरी तनख़्वाह देर से आ रही है",
    "क्या कंपनी मेरा पासपोर्ट रख सकती है?",
    "मैंने यह नौकरी पाने के लिए पैसे दिए",
    "ओवरटाइम का कितना पैसा मिलना चाहिए?",
    "प्रोबेशन कितना लंबा हो सकता है?",
    "मुझे कितना नोटिस देना होगा?",
  ],
  ur: [
    "میری تنخواہ دیر سے آ رہی ہے",
    "کیا کمپنی میرا پاسپورٹ رکھ سکتی ہے؟",
    "میں نے یہ نوکری لینے کے لیے پیسے دیے",
    "اوور ٹائم کا کتنا پیسہ ملنا چاہیے؟",
    "پروبیشن کتنا لمبا ہو سکتا ہے؟",
    "مجھے کتنا نوٹس دینا ہوگا؟",
  ],
  ar: [
    "راتبي متأخر",
    "هل يمكن لشركتي الاحتفاظ بجواز سفري؟",
    "دفعت مالاً للحصول على هذا العمل",
    "كم أجر العمل الإضافي؟",
    "كم مدة فترة التجربة؟",
    "كم مدة الإنذار التي يجب أن أعطيها؟",
  ],
};

type Prepared = { keys: string[]; reply: Omit<AskReply, "kind" | "safety" | "contacts"> };

/** English keywords plus the main Hindi/Urdu words of the starter questions. */
export const PREPARED: Prepared[] = [
  {
    keys: ["salary", "late", "not paid", "unpaid", "wage", "तनख़्वाह", "तनख्वाह", "تنخواہ", "راتب"],
    reply: {
      headline: "Your employer must pay your salary on time.",
      answer:
        "The law says wages must be paid on their due dates, through the system MOHRE approves. If your pay is late, you can report it to MOHRE. MOHRE also has a confidential salary complaint, so your employer is not told who complained.",
      citations: [LAW.art22_2],
      suggest_case: true,
    },
  },
  {
    keys: ["passport", "documents", "पासपोर्ट", "پاسپورٹ", "جواز"],
    reply: {
      headline: "No. Your company cannot keep your passport.",
      answer:
        "The law says your employer must not keep your official documents. Ask for your passport back, in writing if you can. If they refuse, call MOHRE on 80084.",
      citations: [LAW.art13_2],
      suggest_case: true,
    },
  },
  {
    keys: ["fee", "recruitment", "visa cost", "agent", "paid money", "पैसे दिए", "پیسے دیے", "دفعت مالاً"],
    reply: {
      headline: "No. Your employer cannot make you pay for your recruitment.",
      answer:
        "The law forbids charging workers the costs of recruitment and employment, directly or indirectly, for example by cutting your salary. Keep any receipts or messages and tell MOHRE.",
      citations: [LAW.art6_4],
      suggest_case: true,
    },
  },
  {
    keys: ["overtime", "extra hours", "hours", "ओवरटाइम", "اوور ٹائم", "الإضافي"],
    reply: {
      headline: "Overtime is paid at your basic hourly pay plus at least 25%.",
      answer:
        "Normal hours are at most 8 a day or 48 a week. Extra hours are paid at your basic hourly pay plus at least 25%, and overtime between 10 pm and 4 am at plus at least 50% (shift workers excluded).",
      citations: [LAW.art17_1, LAW.art19_2],
      suggest_case: false,
    },
  },
  {
    keys: ["probation", "trial", "प्रोबेशन", "پروبیشن", "التجربة"],
    reply: {
      headline: "Probation can be at most 6 months.",
      answer:
        "Your employer can put you on probation for up to 6 months from your first day. To end your job during probation, they must tell you in writing at least 14 days before.",
      citations: [LAW.art9_1],
      suggest_case: false,
    },
  },
  {
    keys: ["notice", "resign", "quit", "fired", "नोटिस", "نوٹس", "الإنذار"],
    reply: {
      headline: "Notice is what your contract says: at least 30 days, at most 90.",
      answer:
        "Either side can end the contract with written notice. If one side does not give the notice, it must pay the other side the wage for the notice period, or the part that was missed.",
      citations: [LAW.art43_1, LAW.art43_3],
      suggest_case: true,
    },
  },
  {
    keys: ["gratuity", "end of service", "ग्रेच्युटी", "گریجویٹی", "مكافأة نهاية الخدمة"],
    reply: {
      headline: "After 1 year, you get gratuity based on your basic pay.",
      answer:
        "For each of your first 5 years: 21 days of basic pay. For each year after that: 30 days. The total cannot be more than 2 years' pay. Tell me your dates and salary and I can work it out for you.",
      citations: [LAW.art51_2, LAW.art51_6],
      suggest_case: true,
    },
  },
  {
    keys: ["sick", "ill", "hospital", "medical", "बीमार", "بیمار", "مريض", "مرضية"],
    reply: {
      headline: "After probation, you can get up to 90 days of sick leave a year.",
      answer:
        "Tell your employer within 3 working days and give a medical report. The first 15 days are on full pay, the next 30 days on half pay, and the rest unpaid. During probation, sick leave is unpaid.",
      citations: [LAW.art31_3],
      suggest_case: false,
    },
  },
  {
    keys: ["change company", "transfer", "new job", "new company", "change my company"],
    reply: {
      headline: "In many cases, yes: for example when your contract ends.",
      answer:
        "You can move to another employer when your contract ends without being renewed, or when it is ended in the ways the law allows. MOHRE can tell you exactly what applies to you.",
      citations: [LAW.cr27_1],
      suggest_case: false,
    },
  },
  {
    keys: ["contract", "language", "copy", "arabic"],
    reply: {
      headline: "Your contract must be in Arabic and in a language you understand.",
      answer:
        "Your employer must give you your own copy of the contract. It must be in Arabic, plus another language you understand, and both must say the same thing.",
      citations: [LAW.art8_1, LAW.art66_2],
      suggest_case: false,
    },
  },
];

/** The pitch story (illustrative persona, not a real person). */
export const AYESHA_STORY =
  "I worked as a cashier in a supermarket in Abu Dhabi from 1 June 2024. On 20 September my manager told me my job ends today. They gave me no notice. My contract says 30 days' notice. My basic salary is 2,000 dirhams and my total salary is 3,000.";

export const DANGER_EXAMPLE = "My supervisor beats us and locked us in the room.";

/** Facts for the example case, as the confirm card shows them. */
export const EXAMPLE_FACTS: Record<string, string> = {
  emirate: "abu_dhabi",
  worker_type: "private_sector",
  zone: "mainland",
  start_date: "2024-06-01",
  end_date: "2026-09-20",
  total_wage_aed: "3000",
  basic_wage_aed: "2000",
  termination: "employer",
  notice_days_contract: "30",
  notice_days_given: "0",
};

function cite(c: LawClause, quote = c.text_en): Citation {
  const [law, art, cl] = c.chunk_id.split(":");
  return {
    chunk_id: c.chunk_id,
    law_id: law,
    article_no: Number(art.replace("art", "")),
    clause_no: cl ? Number(cl.replace("cl", "")) : null,
    quote,
  };
}

/** The backend's result for the example case (TC-02 facts), so it renders exactly like a live result. */
export const EXAMPLE_ANALYSIS: Analysis = {
  in_scope: true,
  referral: null,
  violations: [
    { issue: "The employer ended the contract without the written notice the contract requires.", article: cite(LAW.art43_1), confidence: "high" },
    { issue: "Notice that was not given must be paid as a notice allowance.", article: cite(LAW.art43_3), confidence: "high" },
    { issue: "More than one year of service: end-of-service gratuity is due.", article: cite(LAW.art51_2), confidence: "high" },
  ],
  not_covered: [],
  claim: [
    {
      item: "Notice pay",
      amount_aed: "3000.00",
      formula: "(30 days' notice − 0 days given) = 30 days × AED 100.00 daily total wage (AED 3,000.00 ÷ 30)",
      article: cite(LAW.art43_3),
      note: "",
    },
    {
      item: "End-of-service gratuity",
      amount_aed: "3229.59",
      formula:
        "842 service days ÷ 365 = 2.3068 years; 2.3068 × 21 = 48.4438 days × AED 66.67 daily basic wage (AED 2,000.00 ÷ 30) = AED 3,229.59",
      article: cite(LAW.art51_2),
      note: "",
    },
  ],
  worker_owes: [],
  total_aed: "6229.59",
  above_mohre_limit: false,
  explanation: "",
  next_steps: [],
  documents_to_gather: [
    "Your contract or offer letter",
    "Bank statements or salary slips",
    "Any message about your job ending",
    "A copy of your labour card or Emirates ID",
  ],
  time_limit_note: "",
  critic_verdict: "pass",
  revised: false,
  writer: {
    headline: "You were let go without notice. You are owed notice pay and gratuity.",
    explanation:
      "Your employer ended your job on the same day, without the 30 days' notice in your contract. The law says they must then pay you your wage for the notice period.\nYou worked for more than 2 years, so you are also owed end-of-service gratuity.",
    amount_lines: [
      "Your wage for the 30 days' notice you did not get.",
      "21 days of basic pay for each year you worked.",
    ],
    checklist: [
      "Ask your employer in writing for your notice pay and gratuity.",
      "If they do not pay, file a complaint with MOHRE (app, website or 80084).",
      "End-of-service dues must be paid within 14 days of your last day.",
    ],
    letter_facts_ar:
      "أعمل أمينة صندوق في متجر في أبوظبي منذ 1 يونيو 2024. في 20 سبتمبر 2026 أبلغني المدير بإنهاء عملي في اليوم نفسه دون أي إنذار، رغم أن عقدي ينص على مدة إنذار 30 يومًا.",
    letter_facts_translation: "",
  },
  writer_failed: false,
  unsure: false,
};

export type XrayRow = { ok: boolean; term: string; law: LawClause | null };

/** Scripted contract X-ray of a synthetic sample contract. */
export const CONTRACT_XRAY: XrayRow[] = [
  { ok: true, term: "Job: cashier. Basic salary 2,000 and total 3,000 a month.", law: null },
  { ok: false, term: "Hours: 9 a day, 6 days a week (54 a week). The normal maximum is 8 a day or 48 a week; extra hours must be paid as overtime.", law: LAW.art17_1 },
  { ok: true, term: "Probation: 6 months. That is the legal maximum.", law: LAW.art9_1 },
  { ok: false, term: "Notice: 120 days. The law allows 30 to 90 days.", law: LAW.art43_1 },
  { ok: true, term: "Annual leave: 30 days a year.", law: LAW.art29_1 },
  { ok: false, term: "Visa costs are taken from your salary. Your employer cannot charge you recruitment costs.", law: LAW.art6_4 },
  { ok: false, term: "The company keeps your passport \"for safekeeping\". This is not allowed.", law: LAW.art13_2 },
  { ok: false, term: "The contract is only in English. It must be in Arabic plus a language you understand.", law: LAW.art66_2 },
];

/** What the sample contract tells the case flow (answers the worker doesn't need to give again). */
export const CONTRACT_PREFILL: Record<string, string> = {
  emirate: "abu_dhabi",
  total_wage_aed: "3000",
  basic_wage_aed: "2000",
  start_date: "2024-06-01",
};
