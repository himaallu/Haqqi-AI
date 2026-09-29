"use client";

import { useEffect, useState } from "react";

import { fetchHealth, type Health } from "@/lib/api";

type State = { kind: "loading" } | { kind: "ok"; health: Health } | { kind: "error" };

export function HealthStatus() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    fetchHealth()
      .then((health) => setState({ kind: "ok", health }))
      .catch(() => setState({ kind: "error" }));
  }, []);

  if (state.kind === "loading") return <p className="text-muted-foreground">backend: checking…</p>;
  if (state.kind === "error") return <p className="text-destructive">backend: unreachable</p>;
  return (
    <p data-testid="health">
      backend: {state.health.status} · db: {state.health.db} · {state.health.version}
    </p>
  );
}
