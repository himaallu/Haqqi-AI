"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ConfirmForm } from "@/components/confirm-form";
import { Progress } from "@/components/progress";
import { Referral } from "@/components/referral";
import { Results } from "@/components/results";
import { Button } from "@/components/ui/button";
import { analyzeCase, getCase } from "@/lib/api";
import { errorMessageKey } from "@/lib/errors";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n/translate";
import type { Analysis, CaseView, Referral as ReferralKind } from "@/lib/types";

type State =
  | { kind: "loading" }
  | { kind: "failed"; message: MessageKey }
  | { kind: "form"; view: CaseView }
  | { kind: "analysing"; view: CaseView; stages: string[]; error: MessageKey | null }
  | { kind: "results"; analysis: Analysis }
  | { kind: "referral"; referral: ReferralKind | null };

/** The backend's `error` event carries an English sentence (haqqi/api/cases.py `_user_message`). */
function streamErrorKey(data: string): MessageKey {
  if (/busy|offline/i.test(data)) return "error.busy";
  if (/could not check/i.test(data)) return "error.invalid";
  return "error.generic";
}

function fromView(view: CaseView): State {
  if (view.status === "out_of_scope") return { kind: "referral", referral: view.referral_kind };
  if (view.status === "analysed" && view.analysis) return { kind: "results", analysis: view.analysis };
  return { kind: "form", view };
}

/** Steps 3–6 for one case. The URL holds only the case id, so a reload picks up where the worker was. */
export function CaseFlow({ caseId }: { caseId: string }) {
  const { lang, t } = useI18n();
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    getCase(caseId)
      .then((view) => setState(fromView(view)))
      .catch((err: unknown) => setState({ kind: "failed", message: errorMessageKey(err) }));
  }, [caseId]);

  // Started from a click, never from an effect, so the analysis runs once per request.
  const analyse = useCallback(
    (view: CaseView) => {
      setState({ kind: "analysing", view, stages: [], error: null });
      const fail = (message: MessageKey) =>
        setState((s) => (s.kind === "analysing" ? { ...s, error: message } : s));
      analyzeCase(caseId, ({ event, data }) => {
        if (event === "done") {
          const analysis = JSON.parse(data) as Analysis;
          setState(
            analysis.in_scope ? { kind: "results", analysis } : { kind: "referral", referral: view.referral_kind },
          );
        } else if (event === "error") {
          fail(streamErrorKey(data));
        } else {
          setState((s) => (s.kind === "analysing" ? { ...s, stages: [...s.stages, event] } : s));
        }
      }).catch((err: unknown) => fail(errorMessageKey(err)));
    },
    [caseId],
  );

  const confirmed = useCallback(
    (view: CaseView) => (view.status === "out_of_scope" ? setState(fromView(view)) : analyse(view)),
    [analyse],
  );

  switch (state.kind) {
    case "loading":
      return <p className="text-muted-foreground">{t("common.loading")}</p>;
    case "failed":
      return (
        <div className="flex flex-col gap-4">
          <p role="alert" className="text-destructive">
            {t(state.message)}
          </p>
          <Button asChild variant="outline">
            <Link href={`/${lang}`}>{t("common.startOver")}</Link>
          </Button>
        </div>
      );
    case "form":
      return <ConfirmForm view={state.view} onConfirmed={confirmed} />;
    case "analysing":
      return (
        <Progress
          stages={state.stages}
          error={state.error}
          onRetry={() => analyse(state.view)}
        />
      );
    case "results":
      return <Results analysis={state.analysis} />;
    case "referral":
      return <Referral kind={state.referral} />;
  }
}
