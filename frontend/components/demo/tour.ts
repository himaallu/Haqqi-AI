/**
 * The guided tour for first-time visitors (e.g. a programme reviewer opening the demo link). It walks through the
 * three doors with the sample content: a question, the sample contract, and Ayesha's case. Each step highlights what
 * to tap and moves on by itself once that happens; explanation steps have a Next button.
 */

/** The parts of a chat message the tour looks at. */
export type TourMsg = { id: number; t: string; stage?: string };

type Text = { title: string; body: string; wait?: string };

export type TourStep = {
  id: string;
  /** CSS selector of what to highlight; the last match (the newest card) wins. */
  target?: string;
  /** Example cards to add to the chat when the step starts, so there is something to tap. */
  enter?: "examples" | "situations";
  /** Messages added since the step started → true when the step is done. Without it the step has a Next button. */
  done?: (added: TourMsg[]) => boolean;
  text: { en: Text; ar: Text };
};

const added = (t: string) => (msgs: TourMsg[]) => msgs.some((m) => m.t === t);

export const TOUR: TourStep[] = [
  {
    id: "welcome",
    text: {
      en: {
        title: "Welcome to Haqqi",
        body: "Haqqi helps migrant workers in the UAE understand their labour rights in their own language. This 2-minute tour shows its three features. Just tap what is highlighted.",
      },
      ar: {
        title: "مرحباً بك في حقّي",
        body: "يساعد حقّي العمال المهاجرين في الإمارات على فهم حقوقهم في العمل بلغتهم. تعرض هذه الجولة القصيرة (دقيقتان) ميزاته الثلاث. اضغط فقط على ما هو مميّز.",
      },
    },
  },
  {
    id: "ask",
    target: '[data-tour="starter-1"]',
    done: (msgs) => msgs.some((m) => m.t === "answer" || m.t === "notice"),
    text: {
      en: {
        title: "1 · Ask a question",
        body: "Workers often have a simple question. Tap this common one.",
        wait: "Haqqi is searching the law…",
      },
      ar: {
        title: "١ · اطرح سؤالاً",
        body: "غالباً ما يكون لدى العامل سؤال بسيط. اضغط على هذا السؤال الشائع.",
        wait: "حقّي يبحث في القانون…",
      },
    },
  },
  {
    id: "answer",
    target: '[data-type="answer"]',
    text: {
      en: {
        title: "A plain answer, backed by law",
        body: "Short, in plain words, in the worker’s language. The chip is the law article it relies on: tap it to read the official text. The AI writes the words; code checks that the article really exists.",
      },
      ar: {
        title: "إجابة بسيطة يدعمها القانون",
        body: "قصيرة وبكلمات بسيطة وبلغة العامل. الزر الصغير هو مادة القانون التي تستند إليها: اضغط عليه لقراءة النص الرسمي. يكتب الذكاء الاصطناعي الكلمات، ويتحقق الكود من وجود المادة فعلاً.",
      },
    },
  },
  {
    id: "contract",
    target: '[data-tour="example-contract"]',
    enter: "examples",
    done: added("contractDoc"),
    text: {
      en: { title: "2 · Check a contract", body: "Many problems start with an unfair contract. Tap the sample contract." },
      ar: { title: "٢ · افحص عقداً", body: "تبدأ مشكلات كثيرة بعقد غير عادل. اضغط على العقد النموذجي." },
    },
  },
  {
    id: "scan",
    target: '[data-tour="check-contract"]',
    done: (msgs) => msgs.some((m) => m.t === "contract" && m.stage === "done"),
    text: {
      en: {
        title: "A contract a worker might sign",
        body: "Read it if you like, then tap “Check this contract”.",
        wait: "Haqqi is reading the contract…",
      },
      ar: {
        title: "عقد قد يوقّعه العامل",
        body: "اقرأه إن شئت، ثم اضغط «افحص هذا العقد».",
        wait: "حقّي يقرأ العقد…",
      },
    },
  },
  {
    id: "xray",
    target: '[data-type="contract"]',
    text: {
      en: {
        title: "Every clause, checked",
        body: "✓ is fine, ⚠ breaks the law, each with the article behind it. Here a 120-day notice, a visa cost taken from salary and the company keeping the passport are all against the law.",
      },
      ar: {
        title: "كل بند تم فحصه",
        body: "✓ سليم، و⚠ يخالف القانون، ومع كل منهما المادة القانونية. هنا: إنذار 120 يوماً، وخصم تكلفة التأشيرة من الراتب، واحتفاظ الشركة بالجواز، كلها مخالفة للقانون.",
      },
    },
  },
  {
    id: "case",
    target: '[data-tour="example-fired"]',
    enter: "situations",
    done: added("facts"),
    text: {
      en: {
        title: "3 · Something went wrong",
        body: "Now a full case. Ayesha, a cashier, was dismissed the same day with no notice. Tap her story.",
        wait: "Haqqi is reading her story…",
      },
      ar: {
        title: "٣ · حدثت مشكلة",
        body: "الآن حالة كاملة. عائشة، أمينة صندوق، فُصلت في اليوم نفسه دون إنذار. اضغط على قصتها.",
        wait: "حقّي يقرأ قصتها…",
      },
    },
  },
  {
    id: "facts",
    target: '[data-tour="confirm-facts"]',
    done: added("result"),
    text: {
      en: {
        title: "Haqqi filled in the facts",
        body: "It read her story (a worker can also speak it, in Urdu or Hindi) and listed the facts. The worker checks them. Tap “Yes, check my case”.",
        wait: "Haqqi is checking the law and calculating her claim…",
      },
      ar: {
        title: "حقّي استخرج الوقائع",
        body: "قرأ قصتها (ويمكن للعامل أن يرويها صوتياً بالأردية أو الهندية) وعرض الوقائع. يراجعها العامل. اضغط «نعم، افحص حالتي».",
        wait: "حقّي يراجع القانون ويحسب مستحقاتها…",
      },
    },
  },
  {
    id: "result",
    target: '[data-type="result"]',
    text: {
      en: {
        title: "Her rights and her claim",
        body: "Each problem cites a law article. Every amount comes from a calculator, not the AI, with its formula shown. Scroll down for next steps and the formal Arabic complaint for MOHRE.",
      },
      ar: {
        title: "حقوقها ومستحقاتها",
        body: "كل مشكلة مع مادة قانونية. وكل مبلغ يحسبه برنامج حاسب، لا الذكاء الاصطناعي، مع المعادلة. مرّر للأسفل لترى الخطوات التالية والشكوى العربية الرسمية للوزارة.",
      },
    },
  },
  {
    id: "end",
    text: {
      en: {
        title: "That’s Haqqi",
        body: "Now try it yourself: type any question, or tap the mic and speak. You can take this tour again from the menu (☰).",
      },
      ar: {
        title: "هذا هو حقّي",
        body: "جرّبه بنفسك الآن: اكتب أي سؤال، أو اضغط على الميكروفون وتحدّث. يمكنك إعادة الجولة من القائمة (☰).",
      },
    },
  },
];

export function tourText(step: TourStep, lang: string): Text {
  return lang === "ar" ? step.text.ar : step.text.en;
}

/** True when the messages added since the step started complete it (steps without `done` wait for Next). */
export function stepDone(step: TourStep, msgs: TourMsg[], since: number): boolean {
  return step.done ? step.done(msgs.filter((m) => m.id >= since)) : false;
}
