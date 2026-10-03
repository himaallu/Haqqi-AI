"use client";

import { createContext, useContext } from "react";

import type { Language } from "../types";

import { HtmlLang } from "./html-lang";
import { languageInfo } from "./languages";
import { translate, type MessageKey, type Vars } from "./translate";

type I18n = { lang: Language; dir: "ltr" | "rtl"; t: (key: MessageKey, vars?: Vars) => string };

const I18nContext = createContext<I18n | null>(null);

export function I18nProvider({ lang, children }: { lang: Language; children: React.ReactNode }) {
  const { dir } = languageInfo(lang);

  const value: I18n = { lang, dir, t: (key, vars) => translate(lang, key, vars) };
  return (
    <I18nContext.Provider value={value}>
      <HtmlLang lang={lang} dir={dir} />
      <div lang={lang} dir={dir} className="flex flex-1 flex-col">
        {children}
      </div>
    </I18nContext.Provider>
  );
}

export function useI18n(): I18n {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used inside I18nProvider");
  return ctx;
}
