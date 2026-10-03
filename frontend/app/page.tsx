import Link from "next/link";

import { HtmlLang } from "@/lib/i18n/html-lang";
import { LANGUAGES } from "@/lib/i18n/languages";
import { translate } from "@/lib/i18n/translate";

// Step 1 of the journey (task 4.2): every option shows its flag and its own script, so no reading of English is needed.
export default function LanguagePicker() {
  return (
    <main className="mx-auto flex w-full max-w-xl flex-1 flex-col gap-6 px-4 py-10">
      <HtmlLang lang="en" dir="ltr" />
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold">
          Haqqi <span lang="ar">حقّي</span>
        </h1>
        <p className="text-muted-foreground">{translate("en", "app.tagline")}</p>
      </header>
      <h2 className="text-lg font-medium">{translate("en", "picker.title")}</h2>
      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2" data-testid="language-list">
        {LANGUAGES.map((l) => (
          <li key={l.code}>
            <Link
              href={`/${l.code}`}
              lang={l.code}
              dir={l.dir}
              className="flex min-h-14 items-center gap-3 rounded-lg border bg-background px-4 py-3 text-lg shadow-xs transition-colors hover:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
            >
              <span aria-hidden className="text-2xl">
                {l.flag}
              </span>
              <span className="flex flex-col">
                <span className="font-medium">{l.native}</span>
                {l.native !== l.english && (
                  <span lang="en" className="text-sm text-muted-foreground">
                    {l.english}
                  </span>
                )}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
