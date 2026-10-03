import { translate } from "@/lib/i18n/translate";
import type { Language } from "@/lib/types";

/** Shown on every screen of a case: English, the worker's language and Arabic, each with MOHRE's 80084. */
export function Disclaimer({ lang }: { lang: Language }) {
  const langs: Language[] = ["en", ...(lang === "en" || lang === "ar" ? [] : [lang]), "ar"];
  return (
    <aside aria-label={translate(lang, "disclaimer.title")} className="flex flex-col gap-2 border-t pt-4 text-xs text-muted-foreground">
      {langs.map((l) => (
        <p key={l} lang={l} dir={l === "ar" || l === "ur" ? "rtl" : "ltr"}>
          {translate(l, "disclaimer.text")}
        </p>
      ))}
    </aside>
  );
}
