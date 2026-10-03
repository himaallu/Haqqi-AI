import type { Language } from "../types";

export type LanguageInfo = {
  code: Language;
  native: string; // the language's name in its own script
  english: string;
  flag: string;
  dir: "ltr" | "rtl";
};

/** The 7 worker languages (PRD) plus Arabic (flag 10), in picker order. */
export const LANGUAGES: LanguageInfo[] = [
  { code: "en", native: "English", english: "English", flag: "🇬🇧", dir: "ltr" },
  { code: "hi", native: "हिन्दी", english: "Hindi", flag: "🇮🇳", dir: "ltr" },
  { code: "ur", native: "اردو", english: "Urdu", flag: "🇵🇰", dir: "rtl" },
  { code: "ml", native: "മലയാളം", english: "Malayalam", flag: "🇮🇳", dir: "ltr" },
  { code: "bn", native: "বাংলা", english: "Bengali", flag: "🇧🇩", dir: "ltr" },
  { code: "tl", native: "Tagalog", english: "Tagalog", flag: "🇵🇭", dir: "ltr" },
  { code: "ne", native: "नेपाली", english: "Nepali", flag: "🇳🇵", dir: "ltr" },
  { code: "ar", native: "العربية", english: "Arabic", flag: "🇦🇪", dir: "rtl" },
];

export function isLanguage(value: string): value is Language {
  return LANGUAGES.some((l) => l.code === value);
}

export function languageInfo(code: Language): LanguageInfo {
  return LANGUAGES.find((l) => l.code === code) ?? LANGUAGES[0];
}
