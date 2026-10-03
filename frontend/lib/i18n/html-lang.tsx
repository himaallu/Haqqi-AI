"use client";

import { useEffect } from "react";

/** Mirrors the page language onto <html>, which the shared root layout renders as English. */
export function HtmlLang({ lang, dir }: { lang: string; dir: "ltr" | "rtl" }) {
  useEffect(() => {
    const html = document.documentElement;
    html.lang = lang;
    html.dir = dir;
  }, [lang, dir]);
  return null;
}
