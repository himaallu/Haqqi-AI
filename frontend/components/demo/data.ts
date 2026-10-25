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
  art53: clause("fdl33-2021:art53", "Payment of Worker's Entitlement at the End of the Contract", "The Employer shall pay the Worker, within fourteen (14) days as of the date of the end of the contract, his wages and all other entitlements stipulated in this Decree by law and the resolutions issued in implementation thereof, the contract or the Establishment's Articles of Association."),
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

type Prepared = {
  keys: string[];
  reply: Omit<AskReply, "kind" | "safety" | "contacts">;
  /** Arabic text of the same answer (today's demo languages are English and Arabic). */
  ar: { headline: string; answer: string };
};

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
    ar: {
      headline: "يجب على صاحب العمل أن يدفع راتبك في موعده.",
      answer: "ينص القانون على دفع الأجور في مواعيد استحقاقها، عبر النظام الذي تعتمده الوزارة. إذا تأخر راتبك، يمكنك إبلاغ وزارة الموارد البشرية والتوطين. ولدى الوزارة شكوى رواتب سرية، فلا يُخبَر صاحب العمل بمن قدّمها.",
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
    ar: {
      headline: "لا. لا يجوز لشركتك الاحتفاظ بجواز سفرك.",
      answer: "ينص القانون على ألا يحتفظ صاحب العمل بالوثائق الرسمية للعامل. اطلب جوازك، كتابةً إن أمكن. وإذا رفضوا، اتصل بالوزارة على 80084.",
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
    ar: {
      headline: "لا. لا يجوز لصاحب العمل أن يُحمّلك تكاليف استقدامك.",
      answer: "يمنع القانون تحميل العامل رسوم وتكاليف الاستقدام والتشغيل، بشكل مباشر أو غير مباشر، مثل الخصم من راتبك. احتفظ بأي إيصالات أو رسائل وأبلغ الوزارة.",
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
    ar: {
      headline: "يُدفع العمل الإضافي بأجرك الأساسي للساعة مع زيادة لا تقل عن 25%.",
      answer: "ساعات العمل العادية لا تزيد على 8 ساعات يومياً أو 48 ساعة أسبوعياً. تُدفع الساعات الإضافية بأجرك الأساسي للساعة مع زيادة لا تقل عن 25%، والعمل الإضافي بين 10 مساءً و4 صباحاً بزيادة لا تقل عن 50% (باستثناء عمال الورديات).",
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
    ar: {
      headline: "لا تزيد فترة التجربة على 6 أشهر.",
      answer: "يجوز لصاحب العمل أن يضعك تحت التجربة مدة لا تزيد على 6 أشهر من أول يوم عمل. ولإنهاء عملك خلال التجربة، يجب أن يُخطرك كتابةً قبل 14 يوماً على الأقل.",
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
    ar: {
      headline: "مدة الإنذار هي ما ينص عليه عقدك: 30 يوماً على الأقل و90 يوماً على الأكثر.",
      answer: "يجوز لأي طرف إنهاء العقد بإنذار كتابي. وإذا لم يلتزم أحد الطرفين بالإنذار، عليه أن يدفع للطرف الآخر أجر مدة الإنذار أو الجزء الذي لم يُنفَّذ منها.",
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
    ar: {
      headline: "بعد سنة من العمل، تستحق مكافأة نهاية الخدمة على أساس أجرك الأساسي.",
      answer: "عن كل سنة من السنوات الخمس الأولى: أجر 21 يوماً. وعن كل سنة بعدها: أجر 30 يوماً. ولا يزيد المجموع على أجر سنتين. أخبرني بتواريخ عملك وراتبك وسأحسبها لك.",
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
    ar: {
      headline: "بعد فترة التجربة، يحق لك إجازة مرضية حتى 90 يوماً في السنة.",
      answer: "أبلغ صاحب العمل خلال 3 أيام عمل وقدّم تقريراً طبياً. أول 15 يوماً بأجر كامل، ثم 30 يوماً بنصف الأجر، والباقي بدون أجر. وخلال فترة التجربة تكون الإجازة المرضية بدون أجر.",
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
    ar: {
      headline: "في حالات كثيرة نعم، مثل انتهاء عقدك.",
      answer: "يمكنك الانتقال إلى صاحب عمل آخر عند انتهاء عقدك دون تجديد، أو عند إنهائه بالطرق التي يسمح بها القانون. ويمكن للوزارة أن تخبرك بما ينطبق عليك تحديداً.",
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
    ar: {
      headline: "يجب أن يكون عقدك بالعربية وبلغة تفهمها.",
      answer: "يجب أن يسلّمك صاحب العمل نسخة من العقد. ويجب أن يكون بالعربية ومعها لغة أخرى تفهمها، وأن يتطابق النصان.",
    },
  },
];

/** The pitch story (illustrative persona, not a real person). */
export const AYESHA_STORY =
  "I worked as a cashier in a supermarket in Abu Dhabi, not in a free zone, from 1 June 2024. On 20 September my manager told me my job ends today. They gave me no notice. My contract says 30 days' notice. My basic salary is 2,000 dirhams and my total salary is 3,000.";

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

export type XrayRow = { ok: boolean; term: string; termAr: string; law: LawClause | null };

/** Scripted contract X-ray of a synthetic sample contract. */
export const CONTRACT_XRAY: XrayRow[] = [
  { ok: true, term: "Job: cashier. Basic salary 2,000 and total 3,000 a month.", termAr: "الوظيفة: أمين صندوق. الراتب الأساسي 2,000 والإجمالي 3,000 شهرياً.", law: null },
  { ok: false, term: "Hours: 9 a day, 6 days a week (54 a week). The normal maximum is 8 a day or 48 a week; extra hours must be paid as overtime.", termAr: "ساعات العمل: 9 يومياً، 6 أيام في الأسبوع (54 ساعة). الحد العادي 8 ساعات يومياً أو 48 أسبوعياً، والساعات الزائدة عمل إضافي مدفوع.", law: LAW.art17_1 },
  { ok: true, term: "Probation: 6 months. That is the legal maximum.", termAr: "فترة التجربة: 6 أشهر، وهي الحد الأقصى القانوني.", law: LAW.art9_1 },
  { ok: false, term: "Notice: 120 days. The law allows 30 to 90 days.", termAr: "مدة الإنذار: 120 يوماً. يسمح القانون بما بين 30 و90 يوماً.", law: LAW.art43_1 },
  { ok: true, term: "Annual leave: 30 days a year.", termAr: "الإجازة السنوية: 30 يوماً في السنة.", law: LAW.art29_1 },
  { ok: false, term: "Visa costs are taken from your salary. Your employer cannot charge you recruitment costs.", termAr: "تُخصم تكاليف التأشيرة من راتبك. لا يجوز لصاحب العمل تحميلك تكاليف الاستقدام.", law: LAW.art6_4 },
  { ok: false, term: "The company keeps your passport \"for safekeeping\". This is not allowed.", termAr: "تحتفظ الشركة بجواز سفرك «للحفظ». هذا غير مسموح.", law: LAW.art13_2 },
  { ok: false, term: "The contract is only in English. It must be in Arabic plus a language you understand.", termAr: "العقد بالإنجليزية فقط. يجب أن يكون بالعربية مع لغة تفهمها.", law: LAW.art66_2 },
];

/** What the sample contract tells the case flow (answers the worker doesn't need to give again). */
export const CONTRACT_PREFILL: Record<string, string> = {
  emirate: "abu_dhabi",
  total_wage_aed: "3000",
  basic_wage_aed: "2000",
  start_date: "2024-06-01",
};

/** The example case in Arabic: same facts, figures and law; Arabic text where the live app writes in the worker's language. */
export const EXAMPLE_ANALYSIS_AR: Analysis = {
  ...EXAMPLE_ANALYSIS,
  claim: EXAMPLE_ANALYSIS.claim.map((line, i) => ({ ...line, item: ["بدل الإنذار", "مكافأة نهاية الخدمة"][i] ?? line.item })),
  documents_to_gather: [
    "عقدك أو عرض العمل",
    "كشوف الحساب البنكي أو قسائم الراتب",
    "أي رسالة عن إنهاء عملك",
    "نسخة من بطاقة العمل أو الهوية الإماراتية",
  ],
  writer: {
    headline: "أُنهي عملك دون إنذار. يحق لك بدل الإنذار ومكافأة نهاية الخدمة.",
    explanation:
      "أنهى صاحب العمل عملك في اليوم نفسه، دون الإنذار المنصوص عليه في عقدك وهو 30 يوماً. وينص القانون على أن يدفع لك في هذه الحالة أجر مدة الإنذار.\nوقد عملت أكثر من سنتين، لذلك تستحق أيضاً مكافأة نهاية الخدمة.",
    amount_lines: ["أجرك عن مدة الإنذار التي لم تحصل عليها، وهي 30 يوماً.", "أجر 21 يوماً من راتبك الأساسي عن كل سنة عملتها."],
    checklist: [
      "اطلب من صاحب العمل كتابةً بدل الإنذار ومكافأة نهاية الخدمة.",
      "إذا لم يدفع، قدّم شكوى إلى الوزارة (التطبيق أو الموقع أو 80084).",
      "يجب دفع مستحقات نهاية الخدمة خلال 14 يوماً من آخر يوم عمل.",
    ],
    letter_facts_ar: EXAMPLE_ANALYSIS.writer?.letter_facts_ar ?? "",
    letter_facts_translation: "",
  },
};

/** The prepared content for a language: Arabic where written, English otherwise. */
export function preparedReply(item: Prepared, lang: string): Prepared["reply"] {
  return lang === "ar" ? { ...item.reply, ...item.ar } : item.reply;
}

type Bilingual = { en: string; ar: string };

/** A sample situation people can try from the home screen: a full story, and its own prepared result for when live AI
 * isn't available. Figures are the backend calculator's output for these facts (eval cases TC-02, TC-23/TC-01, TC-03). */
export type Situation = {
  id: "fired" | "unpaid" | "gratuity";
  icon: string;
  title: Bilingual;
  blurb: Bilingual;
  story: Bilingual;
  facts: Record<string, string>;
  stillEmployed: boolean;
  analysis: { en: Analysis; ar: Analysis };
};

const UNPAID: Analysis = {
  ...EXAMPLE_ANALYSIS,
  violations: [
    { issue: "Two months of wages have not been paid on their due dates.", article: cite(LAW.art22_2), confidence: "high" },
  ],
  claim: [
    { item: "Unpaid wages", amount_aed: "5000.00", formula: "2 month(s) × AED 2,500.00 total monthly wage", article: cite(LAW.art22_2), note: "" },
  ],
  total_aed: "5000.00",
  documents_to_gather: [
    "Bank statements showing the missing salary",
    "Your contract or offer letter",
    "Any message from your employer about the salary",
    "A copy of your labour card or Emirates ID",
  ],
  writer: {
    headline: "Your employer owes you 2 months of salary.",
    explanation:
      "Your employer has not paid your salary for 2 months. The law says wages must be paid on their due dates.\nYou can report this to MOHRE while you keep working.",
    amount_lines: ["Your total salary for the 2 unpaid months."],
    checklist: [
      "Keep proof that you are working (attendance, messages).",
      "If the salary still doesn't come, file a formal complaint with MOHRE (app, website or 80084).",
    ],
    letter_facts_ar:
      "أعمل مساعداً في شركة مقاولات في دبي منذ 1 مارس 2024، وما زلت على رأس عملي. لم يدفع صاحب العمل راتبي عن الشهرين الأخيرين رغم مطالبتي به.",
    letter_facts_translation: "",
  },
};

const GRATUITY: Analysis = {
  ...EXAMPLE_ANALYSIS,
  violations: [
    { issue: "More than 6 years of service: end-of-service gratuity is due and has not been paid.", article: cite(LAW.art51_2), confidence: "high" },
    { issue: "End-of-service dues must be paid within 14 days of the end of the contract.", article: cite(LAW.art53), confidence: "high" },
  ],
  claim: [
    {
      item: "End-of-service gratuity",
      amount_aed: "16056.85",
      formula:
        "2,222 service days ÷ 365 = 6.0877 years; 5.0000 × 21 + 1.0877 × 30 = 137.6301 days × AED 116.67 daily basic wage (AED 3,500.00 ÷ 30) = AED 16,056.85",
      article: cite(LAW.art51_2),
      note: "",
    },
  ],
  total_aed: "16056.85",
  documents_to_gather: [
    "Your contract or offer letter",
    "Your resignation letter and the date it was accepted",
    "Bank statements or salary slips",
    "A copy of your labour card or Emirates ID",
  ],
  writer: {
    headline: "You are owed your end-of-service gratuity.",
    explanation:
      "You worked at the hotel for more than 6 years and resigned with proper notice, so you are owed end-of-service gratuity: 21 days of basic pay for each of the first 5 years, and 30 days for each year after that.\nThe law says it must be paid within 14 days of your last day.",
    amount_lines: ["Your gratuity for just over 6 years of work."],
    checklist: [
      "Ask the hotel in writing for your gratuity.",
      "If it is not paid, file a complaint with MOHRE (app, website or 80084).",
    ],
    letter_facts_ar:
      "عملت في فندق في دبي من 1 أغسطس 2020 حتى 31 أغسطس 2026، واستقلت بعد أن قدّمت إنذاراً مدته 30 يوماً وفق عقدي. ولم يدفع الفندق مكافأة نهاية الخدمة المستحقة لي حتى الآن.",
    letter_facts_translation: "",
  },
};

function arabic(a: Analysis, items: string[], writer: Omit<NonNullable<Analysis["writer"]>, "letter_facts_ar" | "letter_facts_translation">, documents: string[]): Analysis {
  return {
    ...a,
    claim: a.claim.map((line, i) => ({ ...line, item: items[i] ?? line.item })),
    documents_to_gather: documents,
    writer: { ...writer, letter_facts_ar: a.writer?.letter_facts_ar ?? "", letter_facts_translation: "" },
  };
}

export const SITUATIONS: Situation[] = [
  {
    id: "fired",
    icon: "🚪",
    title: { en: "Fired without notice", ar: "فُصلت دون إنذار" },
    blurb: { en: "Ayesha, cashier, Abu Dhabi", ar: "عائشة، أمينة صندوق، أبوظبي" },
    story: {
      en: AYESHA_STORY,
      ar: "عملت أمينة صندوق في سوبرماركت في أبوظبي، ليس في منطقة حرة، منذ 1 يونيو 2024. في 20 سبتمبر أخبرني المدير أن عملي ينتهي اليوم، دون أي إنذار. عقدي ينص على إنذار 30 يوماً. راتبي الأساسي 2,000 درهم وراتبي الإجمالي 3,000 درهم.",
    },
    facts: EXAMPLE_FACTS,
    stillEmployed: false,
    analysis: { en: EXAMPLE_ANALYSIS, ar: EXAMPLE_ANALYSIS_AR },
  },
  {
    id: "unpaid",
    icon: "💰",
    title: { en: "Salary not paid for 2 months", ar: "لم أستلم راتبي منذ شهرين" },
    blurb: { en: "Still working, construction, Dubai", ar: "ما زال يعمل، مقاولات، دبي" },
    story: {
      en: "I work as a helper at a construction company in Dubai, not in a free zone, since 1 March 2024. I have not been paid for the last 2 months. My basic salary is 1,800 dirhams and my total salary is 2,500. I still work there.",
      ar: "أعمل مساعداً في شركة مقاولات في دبي، ليست في منطقة حرة، منذ 1 مارس 2024. لم أستلم راتبي عن آخر شهرين. راتبي الأساسي 1,800 درهم وراتبي الإجمالي 2,500 درهم. ما زلت أعمل في الشركة.",
    },
    facts: {
      termination: "still_employed",
      emirate: "dubai",
      worker_type: "private_sector",
      zone: "mainland",
      start_date: "2024-03-01",
      total_wage_aed: "2500",
      basic_wage_aed: "1800",
    },
    stillEmployed: true,
    analysis: {
      en: UNPAID,
      ar: arabic(
        UNPAID,
        ["الأجور غير المدفوعة"],
        {
          headline: "يدين لك صاحب العمل براتب شهرين.",
          explanation:
            "لم يدفع صاحب العمل راتبك منذ شهرين. وينص القانون على دفع الأجور في مواعيد استحقاقها.\nيمكنك إبلاغ الوزارة وأنت مستمر في عملك.",
          amount_lines: ["راتبك الإجمالي عن الشهرين غير المدفوعين."],
          checklist: [
            "احتفظ بما يثبت أنك تعمل (الحضور، الرسائل).",
            "إذا لم يصل الراتب، قدّم شكوى رسمية إلى الوزارة (التطبيق أو الموقع أو 80084).",
          ],
        },
        ["كشوف الحساب البنكي التي تُظهر الراتب المفقود", "عقدك أو عرض العمل", "أي رسالة من صاحب العمل عن الراتب", "نسخة من بطاقة العمل أو الهوية الإماراتية"],
      ),
    },
  },
  {
    id: "gratuity",
    icon: "🎁",
    title: { en: "Resigned, gratuity not paid", ar: "استقلت ولم أستلم المكافأة" },
    blurb: { en: "6 years at a hotel, Dubai", ar: "6 سنوات في فندق، دبي" },
    story: {
      en: "I worked at a hotel in Dubai, not in a free zone, from 1 August 2020 to 31 August 2026. I resigned and gave 30 days' notice, as my contract says. My basic salary was 3,500 dirhams and my total salary 5,000. The hotel has not paid my end-of-service gratuity.",
      ar: "عملت في فندق في دبي، ليس في منطقة حرة، من 1 أغسطس 2020 حتى 31 أغسطس 2026. استقلت وأعطيت إنذاراً مدته 30 يوماً كما ينص عقدي. كان راتبي الأساسي 3,500 درهم وراتبي الإجمالي 5,000 درهم. لم يدفع الفندق مكافأة نهاية الخدمة.",
    },
    facts: {
      termination: "resigned",
      emirate: "dubai",
      worker_type: "private_sector",
      zone: "mainland",
      start_date: "2020-08-01",
      end_date: "2026-08-31",
      total_wage_aed: "5000",
      basic_wage_aed: "3500",
      notice_days_contract: "30",
      notice_days_given: "30",
    },
    stillEmployed: false,
    analysis: {
      en: GRATUITY,
      ar: arabic(
        GRATUITY,
        ["مكافأة نهاية الخدمة"],
        {
          headline: "يحق لك مكافأة نهاية الخدمة.",
          explanation:
            "عملت في الفندق أكثر من 6 سنوات واستقلت مع إنذار صحيح، لذلك تستحق مكافأة نهاية الخدمة: أجر 21 يوماً من راتبك الأساسي عن كل سنة من السنوات الخمس الأولى، وأجر 30 يوماً عن كل سنة بعدها.\nوينص القانون على دفعها خلال 14 يوماً من آخر يوم عمل.",
          amount_lines: ["مكافأتك عن أكثر من 6 سنوات من العمل."],
          checklist: ["اطلب من الفندق كتابةً مكافأة نهاية الخدمة.", "إذا لم تُدفع، قدّم شكوى إلى الوزارة (التطبيق أو الموقع أو 80084)."],
        },
        ["عقدك أو عرض العمل", "خطاب استقالتك وتاريخ قبولها", "كشوف الحساب البنكي أو قسائم الراتب", "نسخة من بطاقة العمل أو الهوية الإماراتية"],
      ),
    },
  },
];

export function situation(id: string | undefined): Situation {
  return SITUATIONS.find((x) => x.id === id) ?? SITUATIONS[0];
}

/** The synthetic sample contract (docs/demo/SAMPLE_CONTRACT.md); the X-ray rows above match it line by line. */
export const SAMPLE_CONTRACT: { en: string[]; ar: string[] } = {
  en: [
    "EMPLOYMENT CONTRACT",
    "Employer: Bright Mart Supermarkets LLC (example), Abu Dhabi (mainland)",
    "1. Position: Cashier, from 1 June 2024, full-time.",
    "2. Salary: basic AED 2,000; allowances AED 1,000; total AED 3,000 a month.",
    "3. Working hours: 9 hours a day, 6 days a week.",
    "4. Probation: 6 months.",
    "5. Annual leave: 30 days a year.",
    "6. Notice: 120 days' written notice by either party.",
    "7. The visa cost (AED 5,000) is deducted from the employee's salary.",
    "8. The company keeps the employee's passport for safekeeping.",
    "9. This contract is written in English only.",
  ],
  ar: [
    "عقد عمل",
    "صاحب العمل: برايت مارت للسوبرماركت ذ.م.م (مثال)، أبوظبي (البر الرئيسي)",
    "1. الوظيفة: أمين صندوق، من 1 يونيو 2024، بدوام كامل.",
    "2. الراتب: أساسي 2,000 درهم؛ بدلات 1,000 درهم؛ الإجمالي 3,000 درهم شهرياً.",
    "3. ساعات العمل: 9 ساعات يومياً، 6 أيام في الأسبوع.",
    "4. فترة التجربة: 6 أشهر.",
    "5. الإجازة السنوية: 30 يوماً في السنة.",
    "6. الإنذار: 120 يوماً بإنذار كتابي من أي طرف.",
    "7. تُخصم تكلفة التأشيرة (5,000 درهم) من راتب الموظف.",
    "8. تحتفظ الشركة بجواز سفر الموظف للحفظ.",
    "9. هذا العقد مكتوب بالإنجليزية فقط.",
  ],
};
