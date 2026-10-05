"use client";

import { useEffect } from "react";

import { wakeBackend } from "@/lib/api";

/** Starts waking the backend as soon as any page opens (see `wakeBackend`). Renders nothing. */
export function WakeBackend() {
  useEffect(() => {
    void wakeBackend();
  }, []);
  return null;
}
