"use client";

import { AlertTriangle, Camera, FileText, HelpCircle, Loader2, Menu, Mic, Pencil, Phone, Send, Square } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { analyzeCase, apiUrl, ApiError, confirmCase, createCase, fetchHealth, transcribeAudio } from "@/lib/api";
import { LANGUAGES, languageInfo } from "@/lib/i18n/languages";
import { canRecord, formatClock, MAX_RECORDING_SECONDS, pickMimeType } from "@/lib/recorder";
import type { Analysis, CaseView, Language } from "@/lib/types";
import { cn } from "@/lib/utils";

import {
  AnswerCard,
  card,
  ContactButtons,
  ContractCard,
  EmergencyCard,
  FactsCard,
  ghostBtn,
  LawSheet,
  ListenButton,
  primaryBtn,
  ProgressCard,
  QuestionCard,
  ResultCards,
} from "./cards";
import {
  AYESHA_STORY,
  CONTRACT_PREFILL,
  DANGER_EXAMPLE,
  EMERGENCY_CONTACTS,
  EXAMPLE_ANALYSIS,
  EXAMPLE_FACTS,
  MOHRE_CONTACTS,
  PREPARED,
  STARTERS,
} from "./data";
import {
  FIELD_ORDER,
  isDanger,
  kindOf,
  knownFromExtracted,
  matchPrepared,
  nextField,
  parseAmount,
  patchBody,
  type AskReply,
  type Field,
  type Known,
  type LawClause,
} from "./logic";
import { strings, uiLang } from "./strings";

type Msg = { id: number } & (
  | { t: "me"; text: string; voice?: boolean }
  | { t: "say"; text: string; note?: string }
  | { t: "typing"; label: string }
  | { t: "answer"; reply: AskReply }
  | { t: "notice"; kind: "unsure" | "offTopic" }
  | { t: "offer"; seed: string }
  | { t: "emergency" }
  | { t: "question"; field: Field; step: number; steps: number }
  | { t: "facts"; known: Known; example: boolean }
  | { t: "progress"; stages: string[] }
  | { t: "failed"; retry: "analysis" | "story" }
  | { t: "result"; analysis: Analysis; caseId: string | null; stillEmployed: boolean }
  | { t: "referral"; text: string }
  | { t: "contract"; stage: "intro" | "scanning" | "done" }
);
type NewMsg = Msg extends infer M ? (M extends Msg ? Omit<M, "id"> : never) : never;

type Flow =
  | { kind: "idle" }
  | { kind: "story"; prefill: Known }
  | { kind: "questions"; caseId: string; known: Known; answers: Known; field: Field; msgId: number; returnToFacts: boolean }
  | { kind: "facts"; caseId: string | null; known: Known; answers: Known; msgId: number }
  | { kind: "busy" };

const STORE = "haqqi-demo-v1";
const THEME = "haqqi-demo-theme";
const ASK_TIMEOUT_MS = 45_000;

function timeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([promise, new Promise<T>((_, reject) => setTimeout(() => reject(new Error("timeout")), ms))]);
}

async function demoAsk(language: Language, question: string): Promise<AskReply> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ASK_TIMEOUT_MS);
  try {
    const resp = await fetch(apiUrl("/v1/demo/ask"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language, question }),
      signal: controller.signal,
      cache: "no-store",
    });
    if (!resp.ok) throw new ApiError(resp.status, null);
    return (await resp.json()) as AskReply;
  } finally {
    clearTimeout(timer);
  }
}

function loadSaved(): { lang: Language; messages: Msg[] } | null {
  try {
    const raw = localStorage.getItem(STORE);
    return raw ? (JSON.parse(raw) as { lang: Language; messages: Msg[] }) : null;
  } catch {
    return null;
  }
}

function save(lang: Language | null, messages: Msg[]) {
  try {
    if (!lang) return;
    const keep = messages.filter((m) => m.t !== "typing" && m.t !== "progress");
    localStorage.setItem(STORE, JSON.stringify({ lang, messages: keep }));
  } catch {
    // private mode or blocked storage: the demo works without it
  }
}

function clearSaved() {
  try {
    localStorage.removeItem(STORE);
  } catch {
    // ignore
  }
}

/** The pitch demo: one conversation with three doors (docs/CHAT_PLAN.md), on the real backend with a fallback. */
export function DemoApp() {
  const [saved] = useState(loadSaved);
  const [lang, setLang] = useState<Language | null>(saved?.lang ?? null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [resume, setResume] = useState(Boolean(saved?.messages.length));
  const [flow, setFlow] = useState<Flow>({ kind: "idle" });
  const [input, setInput] = useState("");
  const [sheet, setSheet] = useState<LawClause | null>(null);
  const [awake, setAwake] = useState<"waking" | "up" | "down">("waking");
  const [forcedDemo, setForcedDemo] = useState(false);
  const [usedFallback, setUsedFallback] = useState(false);
  const [menu, setMenu] = useState(false);
  const [large, setLarge] = useState(false);
  const [helper, setHelper] = useState(false);
  const [dark, setDark] = useState(() => {
    try {
      return localStorage.getItem(THEME) === "dark";
    } catch {
      return false;
    }
  });
  const [toast, setToast] = useState<string | null>(null);
  const [presenter] = useState(() => new URLSearchParams(window.location.search).has("presenter"));
  const nextId = useRef(1);
  const logoTaps = useRef<number[]>([]);
  const scroller = useRef<HTMLDivElement>(null);

  const s = strings(lang ?? "en");
  const info = languageInfo(lang ?? "en");
  const offline = forcedDemo || awake === "down";

  useEffect(() => {
    let live = true;
    timeout(fetchHealth(), 60_000).then(
      () => live && setAwake("up"),
      () => live && setAwake("down"),
    );
    return () => {
      live = false;
    };
  }, []);

  useEffect(() => {
    save(lang, messages);
  }, [lang, messages]);

  // Bring the first new message into view from its top, so a long result opens on its headline and an answer
  // isn't pushed out of sight by the offer that follows it.
  const seen = useRef(0);
  useEffect(() => {
    const fresh = messages.find((m) => m.id > seen.current && m.t !== "typing");
    if (messages.length) seen.current = Math.max(seen.current, ...messages.map((m) => m.id));
    if (!fresh) return;
    scroller.current?.querySelector(`[data-msg="${fresh.id}"]`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [messages]);

  useEffect(() => {
    document.documentElement.style.fontSize = large ? "118%" : "";
    return () => {
      document.documentElement.style.fontSize = "";
    };
  }, [large]);

  const push = useCallback((...items: NewMsg[]): number => {
    let last = 0;
    const withIds = items.map((m) => {
      last = nextId.current++;
      return { ...m, id: last } as Msg;
    });
    setMessages((cur) => [...cur.filter((m) => m.t !== "typing"), ...withIds]);
    return last;
  }, []);

  const update = useCallback((id: number, patch: Partial<Msg>) => {
    setMessages((cur) => cur.map((m) => (m.id === id ? ({ ...m, ...patch } as Msg) : m)));
  }, []);

  const dropTyping = useCallback(() => setMessages((cur) => cur.filter((m) => m.t !== "typing")), []);

  // Ask door

  const ask = useCallback(
    async (text: string) => {
      if (!lang) return;
      push({ t: "typing", label: s.searching });
      let reply: AskReply | null = null;
      if (!offline) {
        try {
          reply = await demoAsk(lang, text);
        } catch {
          reply = null;
        }
      }
      if (!reply) {
        setUsedFallback(true);
        const match = matchPrepared(text, PREPARED);
        reply = match
          ? { kind: "answer", safety: false, contacts: MOHRE_CONTACTS, ...match.reply }
          : { kind: "unsure", headline: "", answer: "", citations: [], suggest_case: false, safety: false, contacts: MOHRE_CONTACTS };
      }
      const out: NewMsg[] = [];
      if (reply.safety && !isDanger(text)) out.push({ t: "emergency" });
      if (reply.kind === "answer") out.push({ t: "answer", reply });
      else out.push({ t: "notice", kind: reply.kind === "off_topic" ? "offTopic" : "unsure" });
      if (reply.suggest_case) out.push({ t: "offer", seed: text });
      push(...out);
    },
    [lang, offline, push, s.searching],
  );

  // Case door

  const askNext = useCallback(
    (caseId: string, known: Known, answers: Known, returnToFacts = false) => {
      const field = nextField(known);
      if (!field) {
        const msgId = push({ t: "facts", known, example: false });
        setFlow({ kind: "facts", caseId, known, answers, msgId });
        return;
      }
      const remaining = FIELD_ORDER.filter((f) => !known[f]).length;
      const steps = FIELD_ORDER.filter((f) => !(f === "end_date" && known.termination === "still_employed")).length;
      const step = Math.max(1, steps - remaining + 1);
      const msgId = push({ t: "question", field, step, steps });
      setFlow({ kind: "questions", caseId, known, answers, field, msgId, returnToFacts });
    },
    [push],
  );

  const showExample = useCallback(() => {
    setUsedFallback(true);
    const msgId = push(
      { t: "say", text: s.exampleTag, note: "Ayesha (illustrative)" },
      { t: "facts", known: EXAMPLE_FACTS, example: true },
    );
    setFlow({ kind: "facts", caseId: null, known: EXAMPLE_FACTS, answers: {}, msgId });
  }, [push, s.exampleTag]);

  const submitStory = useCallback(
    async (story: string, prefill: Known) => {
      if (!lang) return;
      setFlow({ kind: "busy" });
      push({ t: "typing", label: s.reading });
      if (offline) {
        showExample();
        return;
      }
      let view: CaseView;
      try {
        view = await timeout(createCase({ language: lang, story }), 60_000);
      } catch {
        dropTyping();
        setFlow({ kind: "idle" });
        push({ t: "failed", retry: "story" });
        return;
      }
      if (view.status === "out_of_scope") {
        setFlow({ kind: "idle" });
        push({ t: "referral", text: view.referral ?? "" });
        return;
      }
      const known = { ...knownFromExtracted(view.extracted), ...prefill };
      askNext(view.id, known, { ...prefill });
    },
    [askNext, dropTyping, lang, offline, push, s.reading, showExample],
  );

  const startCase = useCallback(
    (seed?: string, prefill: Known = {}) => {
      if (seed) {
        void submitStory(seed, prefill);
        return;
      }
      push({ t: "say", text: s.tellStory, note: s.privacy });
      setFlow({ kind: "story", prefill });
    },
    [push, s.privacy, s.tellStory, submitStory],
  );

  const answer = useCallback(
    (value: string, label: string) => {
      if (flow.kind !== "questions") return;
      push({ t: "me", text: label });
      const known = { ...flow.known, [flow.field]: value };
      const answers = { ...flow.answers, [flow.field]: value };
      if (flow.returnToFacts) {
        const msgId = push({ t: "facts", known, example: false });
        setFlow({ kind: "facts", caseId: flow.caseId, known, answers, msgId });
        return;
      }
      askNext(flow.caseId, known, answers);
    },
    [askNext, flow, push],
  );

  const editFact = useCallback(
    (field: Field) => {
      if (flow.kind !== "facts" || !flow.caseId) return;
      const msgId = push({ t: "question", field, step: 1, steps: 1 });
      setFlow({ kind: "questions", caseId: flow.caseId, known: flow.known, answers: flow.answers, field, msgId, returnToFacts: true });
    },
    [flow, push],
  );

  const runAnalysis = useCallback(
    async (caseId: string, stillEmployed: boolean) => {
      const progressId = push({ t: "progress", stages: [] });
      const stages: string[] = [];
      let finished = false;
      try {
        await analyzeCase(caseId, ({ event, data }) => {
          if (event === "done") {
            finished = true;
            const analysis = JSON.parse(data) as Analysis;
            setMessages((cur) => cur.filter((m) => m.id !== progressId));
            if (!analysis.in_scope) push({ t: "referral", text: analysis.referral ?? "" });
            else push({ t: "result", analysis, caseId, stillEmployed });
          } else if (event === "error") {
            throw new Error("analysis error");
          } else {
            stages.push(event);
            update(progressId, { stages: [...stages] } as Partial<Msg>);
          }
        });
        if (!finished) throw new Error("stream ended");
      } catch {
        setMessages((cur) => cur.filter((m) => m.id !== progressId));
        push({ t: "failed", retry: "analysis" });
      }
      setFlow({ kind: "idle" });
    },
    [push, update],
  );

  const [pendingCase, setPendingCase] = useState<{ caseId: string; stillEmployed: boolean } | null>(null);

  const confirmFacts = useCallback(async () => {
    if (flow.kind !== "facts") return;
    const { caseId, known, answers } = flow;
    if (!caseId) {
      // the example: play the stages, then the backend's own result for these facts
      setFlow({ kind: "busy" });
      const progressId = push({ t: "progress", stages: [] });
      const order = ["retrieving", "calculating", "analysing", "critiquing", "writing"];
      for (let i = 0; i < order.length; i++) {
        await new Promise((r) => setTimeout(r, 700));
        update(progressId, { stages: order.slice(0, i + 1) } as Partial<Msg>);
      }
      setMessages((cur) => cur.filter((m) => m.id !== progressId));
      push({ t: "result", analysis: EXAMPLE_ANALYSIS, caseId: null, stillEmployed: false });
      setFlow({ kind: "idle" });
      return;
    }
    setFlow({ kind: "busy" });
    try {
      const view = await confirmCase(caseId, patchBody(answers));
      if (view.status === "out_of_scope") {
        push({ t: "referral", text: view.referral ?? "" });
        setFlow({ kind: "idle" });
        return;
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        push({ t: "say", text: s.badFacts });
        const msgId = push({ t: "facts", known, example: false });
        setFlow({ kind: "facts", caseId, known, answers, msgId });
        return;
      }
      push({ t: "failed", retry: "analysis" });
      setFlow({ kind: "idle" });
      return;
    }
    const stillEmployed = known.termination === "still_employed";
    setPendingCase({ caseId, stillEmployed });
    await runAnalysis(caseId, stillEmployed);
  }, [flow, push, runAnalysis, s.badFacts, update]);

  // Contract door

  const openContract = useCallback(() => {
    push({ t: "contract", stage: "intro" });
    setFlow({ kind: "idle" });
  }, [push]);

  const scanContract = useCallback(
    (id: number) => {
      update(id, { stage: "scanning" } as Partial<Msg>);
      setTimeout(() => update(id, { stage: "done" } as Partial<Msg>), 2500);
    },
    [update],
  );

  // Composer

  const send = useCallback(
    (raw: string, voice = false) => {
      const text = raw.trim();
      if (!text || !lang) return;
      setInput("");
      push({ t: "me", text, voice });
      if (isDanger(text)) push({ t: "emergency" });
      if (flow.kind === "story") {
        void submitStory(text, flow.prefill);
        return;
      }
      if (flow.kind === "questions") {
        if (kindOf(flow.field) === "money") {
          const value = parseAmount(text);
          if (value) {
            answer(value, `AED ${Number(value).toLocaleString("en-US")}`);
            return;
          }
        }
        push({ t: "say", text: s.tapAnswer });
        return;
      }
      void ask(text);
    },
    [answer, ask, flow, lang, push, s.tapAnswer, submitStory],
  );

  const reset = useCallback(() => {
    setMessages([]);
    setFlow({ kind: "idle" });
    setInput("");
    setPendingCase(null);
    clearSaved();
  }, []);

  useEffect(() => {
    if (!presenter) return;
    function onKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLSelectElement) return;
      if (e.key === "r" || e.key === "R") reset();
      if (e.key === "1") send(STARTERS.en[1]);
      if (e.key === "2") startCase(AYESHA_STORY);
      if (e.key === "3") openContract();
      if (e.key === "4") send(DANGER_EXAMPLE);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [openContract, presenter, reset, send, startCase]);

  function tapLogo() {
    const now = Date.now();
    logoTaps.current = [...logoTaps.current.filter((t) => now - t < 3000), now];
    if (logoTaps.current.length >= 5) {
      logoTaps.current = [];
      setForcedDemo((v) => !v);
    }
  }

  function flash(text: string) {
    setToast(text);
    setTimeout(() => setToast(null), 2500);
  }

  const activeId = flow.kind === "questions" || flow.kind === "facts" ? flow.msgId : null;
  const lastId = messages[messages.length - 1]?.id;
  const locale = lang === "ur" ? "ur-PK" : lang === "hi" ? "hi-IN" : lang === "ar" ? "ar-AE" : "en-GB";
  const starters = STARTERS[uiLang(lang ?? "en")];

  const phone = (
    <div
      lang={lang ?? "en"}
      dir={info.dir}
      className="relative flex h-dvh w-full flex-col overflow-hidden bg-d-bg text-d-ink lg:h-[844px] lg:w-[390px] lg:rounded-[44px] lg:border-[10px] lg:border-[#151a1a] lg:shadow-2xl"
    >
      {!lang ? (
        <LanguagePicker
          onPick={(l) => {
            setLang(l);
            reset();
          }}
        />
      ) : (
        <>
          <header className="flex items-center justify-between gap-2 border-b border-d-line bg-d-card px-4 py-2">
            <button type="button" onClick={tapLogo} className="flex items-baseline gap-1.5 text-lg font-semibold text-d-primary" aria-label="Haqqi">
              Haqqi
              <span lang="ar" className="font-[family-name:var(--font-noto-arabic)]">
                حقّي
              </span>
            </button>
            <div className="flex items-center gap-1">
              {awake === "waking" && !forcedDemo && (
                <span className="flex items-center gap-1 rounded-full bg-d-primary-soft px-2 py-1 text-xs text-d-primary">
                  <Loader2 aria-hidden className="size-3 animate-spin" />
                  {s.waking}
                </span>
              )}
              {(offline || usedFallback) && <span className="rounded-full bg-d-line px-2 py-1 text-xs text-d-muted">{s.demoMode}</span>}
              <button type="button" onClick={() => setLang(null)} className="rounded-full p-2 text-xl" aria-label="Language">
                {info.flag}
              </button>
              <a href="tel:80084" className="rounded-full p-2 text-d-primary" aria-label="Call MOHRE 80084">
                <Phone className="size-5" />
              </a>
              <a href="https://wa.me/971600590000" target="_blank" rel="noreferrer" className="rounded-full p-2 text-d-ok" aria-label="MOHRE WhatsApp">
                <WhatsAppIcon />
              </a>
              <button type="button" onClick={() => setMenu((v) => !v)} className="rounded-full p-2" aria-label="Menu" aria-expanded={menu}>
                <Menu className="size-5" />
              </button>
            </div>
          </header>
          {menu && (
            <div className="absolute end-3 top-14 z-20 flex w-60 flex-col gap-1 rounded-2xl border border-d-line bg-d-card p-2 shadow-lg">
              <label className="flex min-h-11 items-center justify-between gap-2 px-3">
                {s.largeText}
                <input type="checkbox" checked={large} onChange={(e) => setLarge(e.target.checked)} className="size-5 accent-d-primary" />
              </label>
              <label className="flex min-h-11 items-center justify-between gap-2 px-3">
                {s.helper}
                <input type="checkbox" checked={helper} onChange={(e) => setHelper(e.target.checked)} className="size-5 accent-d-primary" />
              </label>
              <label className="flex min-h-11 items-center justify-between gap-2 px-3">
                {s.darkMode}
                <input
                  type="checkbox"
                  checked={dark}
                  onChange={(e) => {
                    setDark(e.target.checked);
                    try {
                      localStorage.setItem(THEME, e.target.checked ? "dark" : "light");
                    } catch {
                      // the choice just won't be remembered
                    }
                  }}
                  className="size-5 accent-d-primary"
                />
              </label>
              <button
                type="button"
                className="min-h-11 rounded-xl px-3 text-start text-d-danger hover:bg-d-danger-bg"
                onClick={() => {
                  reset();
                  setMenu(false);
                  flash(s.deleted);
                }}
              >
                {s.deleteChat}
              </button>
            </div>
          )}

          <div ref={scroller} className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-4" aria-live="polite">
            {resume && saved && (
              <div className={cn(card, "flex flex-col gap-3")}>
                <p className="font-medium">{s.resume}</p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    className={primaryBtn}
                    onClick={() => {
                      nextId.current = Math.max(0, ...saved.messages.map((m) => m.id)) + 1;
                      setMessages(saved.messages);
                      setResume(false);
                    }}
                  >
                    {s.resumeYes}
                  </button>
                  <button
                    type="button"
                    className={ghostBtn}
                    onClick={() => {
                      reset();
                      setResume(false);
                    }}
                  >
                    {s.resumeNo}
                  </button>
                </div>
              </div>
            )}

            {helper && (
              <p className="rounded-xl bg-d-primary-soft px-3 py-2 text-sm text-d-primary">
                {s.helper}: the answers describe the worker&apos;s rights.
              </p>
            )}

            <HaqqiBubble>
              <p>{s.greeting}</p>
              <ListenButton text={s.greeting} lang={lang} s={s} />
            </HaqqiBubble>

            {messages.length === 0 && (
              <>
                <div className="flex flex-col gap-2">
                  <Door icon={<HelpCircle className="size-6" />} label={s.doorAsk} onClick={() => document.getElementById("demo-input")?.focus()} />
                  <Door icon={<FileText className="size-6" />} label={s.doorContract} onClick={openContract} />
                  <Door icon={<AlertTriangle className="size-6" />} label={s.doorProblem} onClick={() => startCase()} tone="warn" />
                </div>
                <p className="mt-2 text-sm font-medium text-d-muted">{s.peopleAsk}</p>
                <div className="flex flex-wrap gap-2">
                  {starters.map((q) => (
                    <button key={q} type="button" onClick={() => send(q)} className="min-h-11 rounded-full border border-d-line bg-d-card px-4 py-2 text-start text-sm hover:border-d-primary">
                      {q}
                    </button>
                  ))}
                </div>
              </>
            )}

            {messages.map((m) => (
              <div key={m.id} data-msg={m.id} className="scroll-mt-3">
              <MessageView
                m={m}
                active={m.id === activeId || (m.id === lastId && flow.kind === "idle")}
                busy={flow.kind === "busy"}
                lang={lang}
                locale={locale}
                s={s}
                onLaw={setSheet}
                onAnswer={answer}
                onEditFact={editFact}
                onConfirm={() => void confirmFacts()}
                onStartCase={(seed) => startCase(seed)}
                onFix={(text) => {
                  setInput(text);
                  document.getElementById("demo-input")?.focus();
                }}
                onContractStart={scanContract}
                onContractUse={() => startCase(undefined, CONTRACT_PREFILL)}
                onRetry={(kind) => {
                  if (kind === "analysis" && pendingCase) void runAnalysis(pendingCase.caseId, pendingCase.stillEmployed);
                  else startCase();
                }}
                onExample={showExample}
                onDoors={{ ask: () => document.getElementById("demo-input")?.focus(), contract: openContract, problem: () => startCase() }}
              />
              </div>
            ))}
          </div>

          <footer className="border-t border-d-line bg-d-card px-3 pt-2 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
            <p className="mb-2 text-center text-[11px] leading-tight text-d-muted">{s.disclaimer}</p>
            <Composer
              value={input}
              onChange={setInput}
              onSend={(text, voice) => send(text, voice)}
              onCamera={openContract}
              disabled={flow.kind === "busy"}
              lang={lang}
              s={s}
              offline={offline}
            />
          </footer>
          {sheet && <LawSheet clause={sheet} onClose={() => setSheet(null)} s={s} />}
          {toast && (
            <div className="absolute inset-x-0 bottom-28 z-40 mx-auto w-fit rounded-full bg-d-ink px-4 py-2 text-sm text-d-bg shadow-lg">{toast}</div>
          )}
        </>
      )}
    </div>
  );

  return (
    <div data-theme={dark ? "dark" : "light"} className="demo min-h-dvh bg-d-bg text-d-ink lg:flex lg:items-center lg:justify-center lg:gap-16 lg:p-8">
      <aside className="hidden max-w-sm flex-col gap-6 lg:flex">
        <p className="text-4xl font-semibold text-d-primary">
          Haqqi <span lang="ar">حقّي</span>
        </p>
        <p className="text-2xl leading-snug">Your rights at work, in your language.</p>
        <ul className="flex flex-col gap-3 text-lg text-d-muted">
          <li>🎙️ Speak in your own language</li>
          <li>📖 Every answer cites the law</li>
          <li>🧮 Every amount from a calculator, not AI</li>
          <li>📄 A formal Arabic complaint, ready for MOHRE</li>
        </ul>
        {presenter && (
          <p className="rounded-xl border border-d-line p-3 text-sm text-d-muted">
            Presenter keys: 1 passport · 2 Ayesha · 3 contract · 4 danger · R reset · tap logo ×5 = demo mode
            {forcedDemo ? " (on)" : ""}
          </p>
        )}
      </aside>
      {phone}
    </div>
  );
}

function LanguagePicker({ onPick }: { onPick: (l: Language) => void }) {
  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-8">
      <p className="text-3xl font-semibold text-d-primary">
        Haqqi <span lang="ar">حقّي</span>
      </p>
      <p className="text-d-muted">Choose your language · अपनी भाषा चुनें · اپنی زبان منتخب کریں</p>
      <ul className="flex flex-col gap-2">
        {LANGUAGES.map((l) => (
          <li key={l.code}>
            <button
              type="button"
              lang={l.code}
              dir={l.dir}
              onClick={() => onPick(l.code)}
              className="flex min-h-14 w-full items-center gap-3 rounded-2xl border border-d-line bg-d-card px-4 py-3 text-start text-lg shadow-sm hover:border-d-primary"
            >
              <span aria-hidden className="text-2xl">
                {l.flag}
              </span>
              <span className="flex flex-col">
                <span className="font-medium">{l.native}</span>
                {l.native !== l.english && <span className="text-sm text-d-muted">{l.english}</span>}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Door({ icon, label, onClick, tone }: { icon: React.ReactNode; label: string; onClick: () => void; tone?: "warn" }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "demo-in flex min-h-16 items-center gap-4 rounded-2xl border bg-d-card px-4 py-3 text-start text-lg font-medium shadow-sm transition-colors",
        tone === "warn" ? "border-d-warn/30 hover:bg-d-warn-bg" : "border-d-line hover:bg-d-primary-soft",
      )}
    >
      <span className={cn("rounded-xl p-2", tone === "warn" ? "bg-d-warn-bg text-d-warn" : "bg-d-primary-soft text-d-primary")}>{icon}</span>
      {label}
    </button>
  );
}

function HaqqiBubble({ children }: { children: React.ReactNode }) {
  return (
    <div className="demo-in flex items-start gap-2">
      <span aria-hidden className="mt-1 flex size-8 shrink-0 items-center justify-center rounded-full bg-d-primary text-sm font-bold text-d-on-primary">
        ح
      </span>
      <div className="flex max-w-[85%] flex-col gap-1 rounded-2xl rounded-ss-sm bg-d-card px-4 py-3 shadow-sm">{children}</div>
    </div>
  );
}

type ViewProps = {
  m: Msg;
  active: boolean;
  busy: boolean;
  lang: Language;
  locale: string;
  s: ReturnType<typeof strings>;
  onLaw: (c: LawClause) => void;
  onAnswer: (value: string, label: string) => void;
  onEditFact: (f: Field) => void;
  onConfirm: () => void;
  onStartCase: (seed?: string) => void;
  onFix: (text: string) => void;
  onContractStart: (id: number) => void;
  onContractUse: () => void;
  onRetry: (kind: "analysis" | "story") => void;
  onExample: () => void;
  onDoors: { ask: () => void; contract: () => void; problem: () => void };
};

function MessageView(p: ViewProps) {
  const { m, s } = p;
  switch (m.t) {
    case "me":
      return (
        <div className="demo-in flex flex-col items-end gap-1">
          <p dir="auto" className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-se-sm bg-d-me px-4 py-3 text-d-on-me">
            {m.text}
          </p>
          {m.voice && (
            <button type="button" onClick={() => p.onFix(m.text)} className="flex items-center gap-1 text-xs text-d-muted">
              <Pencil aria-hidden className="size-3" /> {s.fix}
            </button>
          )}
        </div>
      );
    case "say":
      return (
        <HaqqiBubble>
          <p>{m.text}</p>
          {m.note && <p className="rounded-lg bg-d-warn-bg px-2 py-1 text-sm text-d-warn">{m.note}</p>}
        </HaqqiBubble>
      );
    case "typing":
      return (
        <HaqqiBubble>
          <p className="flex items-center gap-2 text-d-muted">
            <Loader2 aria-hidden className="size-4 animate-spin" />
            {m.label}
          </p>
        </HaqqiBubble>
      );
    case "answer":
      return <AnswerCard reply={m.reply} lang={p.lang} s={s} onLaw={p.onLaw} />;
    case "notice":
      return (
        <div className={cn(card, "flex flex-col gap-3")}>
          <p>{m.kind === "unsure" ? s.unsure : s.offTopic}</p>
          {m.kind === "unsure" ? (
            <ContactButtons contacts={MOHRE_CONTACTS} />
          ) : (
            <div className="flex flex-wrap gap-2">
              <button type="button" className={ghostBtn} onClick={p.onDoors.ask}>
                {s.doorAsk}
              </button>
              <button type="button" className={ghostBtn} onClick={p.onDoors.contract}>
                {s.doorContract}
              </button>
              <button type="button" className={ghostBtn} onClick={p.onDoors.problem}>
                {s.doorProblem}
              </button>
            </div>
          )}
        </div>
      );
    case "offer":
      return (
        <div className={cn(card, "flex flex-col gap-3 border-d-primary/40 bg-d-primary-soft")}>
          <p>{s.offer}</p>
          {p.active && (
            <div className="flex flex-wrap gap-2">
              <button type="button" className={primaryBtn} onClick={() => p.onStartCase()}>
                {s.checkCase}
              </button>
            </div>
          )}
        </div>
      );
    case "emergency":
      return <EmergencyCard contacts={[...EMERGENCY_CONTACTS, ...MOHRE_CONTACTS]} s={s} />;
    case "question":
      return <QuestionCard field={m.field} step={m.step} steps={m.steps} active={p.active} s={s} locale={p.locale} onAnswer={p.onAnswer} />;
    case "facts":
      return (
        <FactsCard
          known={m.known}
          active={p.active}
          example={m.example}
          busy={p.busy}
          s={s}
          locale={p.locale}
          onEdit={p.onEditFact}
          onConfirm={p.onConfirm}
        />
      );
    case "progress":
      return <ProgressCard stages={m.stages} s={s} />;
    case "failed":
      return (
        <div className={cn(card, "flex flex-col gap-3")}>
          <p>{s.busy}</p>
          <div className="flex flex-wrap gap-2">
            <button type="button" className={primaryBtn} onClick={() => p.onRetry(m.retry)}>
              {s.retry}
            </button>
            <button type="button" className={ghostBtn} onClick={p.onExample}>
              {s.example}
            </button>
          </div>
          <ContactButtons contacts={MOHRE_CONTACTS.slice(0, 1)} />
        </div>
      );
    case "result":
      return <ResultCards analysis={m.analysis} caseId={m.caseId} stillEmployed={m.stillEmployed} lang={p.lang} s={s} onLaw={p.onLaw} />;
    case "referral":
      return (
        <div className={cn(card, "flex flex-col gap-3")}>
          <p className="font-semibold">{s.referral}</p>
          <p dir="ltr" lang="en" className="text-start">
            {m.text}
          </p>
          <ContactButtons contacts={MOHRE_CONTACTS} />
        </div>
      );
    case "contract":
      return (
        <ContractCard
          stage={m.stage}
          active={p.active}
          s={s}
          onStart={() => p.onContractStart(m.id)}
          onUse={p.onContractUse}
          onLaw={p.onLaw}
        />
      );
  }
}

type RecState = { kind: "idle" } | { kind: "recording"; seconds: number } | { kind: "sending" };

function Composer(props: {
  value: string;
  onChange: (v: string) => void;
  onSend: (text: string, voice: boolean) => void;
  onCamera: () => void;
  disabled: boolean;
  lang: Language;
  s: ReturnType<typeof strings>;
  offline: boolean;
}) {
  const { value, onChange, onSend, onCamera, disabled, lang, s, offline } = props;
  const [rec, setRec] = useState<RecState>({ kind: "idle" });
  const [error, setError] = useState<string | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(
    () => () => {
      if (timer.current) clearInterval(timer.current);
      recorder.current?.stream.getTracks().forEach((t) => t.stop());
    },
    [],
  );

  async function start() {
    setError(null);
    if (!canRecord() || offline) {
      setError(s.micNone);
      return;
    }
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError(s.micDenied);
      return;
    }
    const mimeType = pickMimeType((t) => MediaRecorder.isTypeSupported(t));
    const r = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    const chunks: Blob[] = [];
    r.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    r.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      setRec({ kind: "sending" });
      try {
        const { text } = await transcribeAudio(new Blob(chunks, { type: r.mimeType || mimeType || "audio/webm" }), lang);
        if (text.trim()) onSend(text, true);
        else setError(s.heardNothing);
      } catch {
        setError(s.heardNothing);
      }
      setRec({ kind: "idle" });
    };
    recorder.current = r;
    r.start(1000);
    setRec({ kind: "recording", seconds: 0 });
    timer.current = setInterval(() => {
      setRec((cur) => {
        if (cur.kind !== "recording") return cur;
        if (cur.seconds + 1 >= MAX_RECORDING_SECONDS) stop();
        return { kind: "recording", seconds: cur.seconds + 1 };
      });
    }, 1000);
  }

  function stop() {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    if (recorder.current && recorder.current.state !== "inactive") recorder.current.stop();
  }

  if (rec.kind === "recording") {
    return (
      <div className="flex min-h-14 items-center gap-3 rounded-full bg-d-danger-bg px-4">
        <span className="relative flex size-3">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-d-danger opacity-75" />
          <span className="relative inline-flex size-3 rounded-full bg-d-danger" />
        </span>
        <span className="flex-1 font-medium text-d-danger">{s.listening}</span>
        <span dir="ltr" className="font-mono text-d-danger">
          {formatClock(rec.seconds)}
        </span>
        <button type="button" onClick={stop} className="flex size-11 items-center justify-center rounded-full bg-d-danger text-white" aria-label={s.stop}>
          <Square className="size-5" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      {error && <p className="px-2 text-xs text-d-danger">{error}</p>}
      <form
        className="flex items-center gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          onSend(value, false);
        }}
      >
        <button type="button" onClick={onCamera} className="flex size-11 shrink-0 items-center justify-center rounded-full text-d-muted hover:bg-d-primary-soft" aria-label={s.doorContract}>
          <Camera className="size-5" />
        </button>
        <input
          id="demo-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={s.placeholder}
          maxLength={1000}
          disabled={disabled || rec.kind === "sending"}
          className="min-h-12 min-w-0 flex-1 rounded-full border border-d-line bg-d-bg px-4 text-base outline-none focus:border-d-primary"
        />
        {value.trim() ? (
          <button type="submit" className="flex size-14 shrink-0 items-center justify-center rounded-full bg-d-primary text-d-on-primary" aria-label="Send" disabled={disabled}>
            <Send className="size-6 rtl:-scale-x-100" />
          </button>
        ) : (
          <button
            type="button"
            onClick={() => void start()}
            disabled={disabled || rec.kind === "sending"}
            className="flex size-14 shrink-0 items-center justify-center rounded-full bg-d-primary text-d-on-primary shadow-md"
            aria-label={s.listen}
          >
            {rec.kind === "sending" ? <Loader2 className="size-6 animate-spin" /> : <Mic className="size-6" />}
          </button>
        )}
      </form>
    </div>
  );
}

function WhatsAppIcon() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" fill="currentColor" aria-hidden>
      <path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.1l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.2-.4.7-1.4a.5.5 0 0 0 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 11.9 11.9 0 0 0 4.6 4c1.7.7 2.4.8 3.2.7a2.8 2.8 0 0 0 1.8-1.3 2.3 2.3 0 0 0 .2-1.3c-.1-.1-.3-.2-.5-.3Z" />
    </svg>
  );
}
