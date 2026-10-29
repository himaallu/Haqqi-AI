"use client";

import { Loader2, X } from "lucide-react";
import { useEffect, useRef, useState, type RefObject } from "react";

import { primaryBtn } from "./cards";
import type { Strings } from "./strings";
import { tourText, type TourStep } from "./tour";

type Box = { left: number; top: number; width: number; height: number };

/** The tour's guide card (pinned under the header) and a ring around what to tap next. */
export function TourGuide(props: {
  step: TourStep;
  index: number;
  total: number;
  lang: string;
  waiting: boolean;
  frame: RefObject<HTMLDivElement | null>;
  s: Strings;
  onNext: () => void;
  onSkip: () => void;
}) {
  const { step, index, total, lang, waiting, frame, s, onNext, onSkip } = props;
  const text = tourText(step, lang);
  const [box, setBox] = useState<Box | null>(null);
  const card = useRef<HTMLDivElement>(null);
  const seen = useRef<{ el: Element; at: number; scrolled: boolean } | null>(null);

  // Follow the target as the chat grows and scrolls. Shortly after it first appears (once the chat's own scroll to
  // new messages is done), scroll its top to just below the guide card (cards like the answer grow as they appear).
  useEffect(() => {
    let raf = 0;
    const tick = () => {
      const frameEl = frame.current;
      const matches = step.target ? document.querySelectorAll(step.target) : [];
      const el = matches.length ? matches[matches.length - 1] : null;
      if (el && frameEl) {
        if (seen.current?.el !== el) seen.current = { el, at: performance.now(), scrolled: false };
        const scroller = el.closest(".overflow-y-auto");
        const age = performance.now() - seen.current.at;
        if (scroller && card.current && age > 400) {
          const delta = el.getBoundingClientRect().top - (card.current.getBoundingClientRect().bottom + 12);
          if (!seen.current.scrolled) {
            seen.current.scrolled = true;
            scroller.scrollBy({ top: delta, behavior: "smooth" });
          } else if (age > 1200 && age < 5000 && delta < -8) {
            // Cards that reveal their text scroll themselves when done; keep the top visible for the first seconds.
            scroller.scrollBy({ top: delta });
          }
        }
        const r = el.getBoundingClientRect();
        const f = frameEl.getBoundingClientRect();
        const next = { left: r.left - f.left - 4, top: r.top - f.top - 4, width: r.width + 8, height: r.height + 8 };
        setBox((cur) =>
          cur && Math.abs(cur.left - next.left) < 1 && Math.abs(cur.top - next.top) < 1 && Math.abs(cur.height - next.height) < 1
            ? cur
            : next,
        );
      } else {
        setBox((cur) => (cur ? null : cur));
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [frame, step]);

  const last = index === total - 1;
  return (
    <>
      {box && (
        <div
          aria-hidden
          className="pointer-events-none absolute z-20 animate-pulse rounded-2xl border-[3px] border-d-accent shadow-[0_0_0_6px_rgba(232,162,58,0.25)]"
          style={{ left: box.left, top: box.top, width: box.width, height: box.height }}
        />
      )}
      <div ref={card} role="dialog" aria-label={s.tourName} className="demo-in absolute inset-x-3 top-14 z-30 flex flex-col gap-1.5 rounded-2xl border-2 border-d-accent bg-d-card p-3 shadow-xl">
        <div className="flex items-center justify-between gap-2 text-xs font-medium text-d-muted">
          <span>
            🧭 {s.tourName} · {index + 1}/{total}
          </span>
          <button type="button" onClick={onSkip} className="flex min-h-8 items-center gap-1 rounded-full px-2 hover:bg-d-primary-soft" aria-label={s.tourSkip}>
            {s.tourSkip}
            <X aria-hidden className="size-3.5" />
          </button>
        </div>
        <p className="font-semibold leading-snug text-d-ink">{text.title}</p>
        <p className="text-sm leading-snug text-d-ink">{text.body}</p>
        {waiting && text.wait ? (
          <p className="flex items-center gap-1.5 text-sm text-d-primary">
            <Loader2 aria-hidden className="size-4 animate-spin" />
            {text.wait}
          </p>
        ) : step.done ? (
          <p className="text-xs font-medium text-d-primary">👆 {s.tourTap}</p>
        ) : (
          <button type="button" onClick={onNext} className={`${primaryBtn} mt-1 self-end`}>
            {index === 0 ? s.tourStart : last ? s.tourFinish : s.tourNext}
          </button>
        )}
      </div>
    </>
  );
}
