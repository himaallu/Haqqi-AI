"use client";

import { Check, Circle, LoaderCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n/translate";

// Stage events from POST /v1/cases/{id}/analyze, in order. "revising" appears only when the Critic asks for it.
const STAGES = ["retrieving", "calculating", "analysing", "critiquing", "revising", "writing"] as const;
type Stage = (typeof STAGES)[number];

const LABELS: Record<Stage, MessageKey> = {
  retrieving: "stage.retrieving",
  calculating: "stage.calculating",
  analysing: "stage.analysing",
  critiquing: "stage.critiquing",
  revising: "stage.revising",
  writing: "stage.writing",
};

/** Task 4.5: ticks each agent stage as it streams in. */
export function Progress({
  stages,
  error,
  onRetry,
}: {
  stages: string[];
  error: MessageKey | null;
  onRetry: () => void;
}) {
  const { t } = useI18n();
  const current = stages.at(-1);
  const reached = STAGES.findIndex((s) => s === current);
  const shown = STAGES.filter((s) => s !== "revising" || stages.includes("revising"));

  return (
    <section className="flex flex-col gap-4" aria-live="polite">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">{t("progress.title")}</h1>
        <p className="text-muted-foreground">{t("progress.help")}</p>
      </div>
      <ol className="flex flex-col gap-3" data-testid="stages">
        {shown.map((stage) => {
          const index = STAGES.indexOf(stage);
          const status = index < reached ? "done" : index === reached && !error ? "active" : "pending";
          return (
            <li key={stage} data-status={status} className="flex items-center gap-3">
              {status === "done" && <Check aria-hidden className="size-5 text-success" />}
              {status === "active" && <LoaderCircle aria-hidden className="size-5 animate-spin" />}
              {status === "pending" && <Circle aria-hidden className="size-5 text-muted-foreground/40" />}
              <span className={status === "pending" ? "text-muted-foreground" : ""}>{t(LABELS[stage])}</span>
            </li>
          );
        })}
      </ol>
      {error && (
        <div className="flex flex-col gap-3">
          <p role="alert" data-testid="progress-error" className="text-destructive">
            {t(error)}
          </p>
          <Button onClick={onRetry}>{t("common.retry")}</Button>
        </div>
      )}
    </section>
  );
}
