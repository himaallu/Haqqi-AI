import type { Language } from "../types";

import ar from "./catalogs/ar.json";
import bn from "./catalogs/bn.json";
import en from "./catalogs/en.json";
import hi from "./catalogs/hi.json";
import ml from "./catalogs/ml.json";
import ne from "./catalogs/ne.json";
import tl from "./catalogs/tl.json";
import ur from "./catalogs/ur.json";

export type MessageKey = keyof typeof en;
export type Catalog = Partial<Record<MessageKey | "_note", string>>;
export type Vars = Record<string, string | number>;

/** UI strings. Non-English catalogs are drafts until a native speaker reviews them (task 6.3). */
export const CATALOGS: Record<Language, Catalog> = { en, hi, ur, ml, bn, tl, ne, ar };

export function translate(lang: Language, key: MessageKey, vars: Vars = {}): string {
  let text = CATALOGS[lang][key];
  if (text === undefined) {
    console.warn(`i18n: missing "${key}" in ${lang}`);
    text = en[key] ?? key;
  }
  return text.replace(/\{(\w+)\}/g, (match, name: string) => (name in vars ? String(vars[name]) : match));
}
