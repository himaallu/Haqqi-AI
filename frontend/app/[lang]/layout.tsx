import Link from "next/link";
import { notFound } from "next/navigation";

import { Disclaimer } from "@/components/disclaimer";
import { I18nProvider } from "@/lib/i18n/provider";
import { LANGUAGES, isLanguage, languageInfo } from "@/lib/i18n/languages";
import { translate } from "@/lib/i18n/translate";

export function generateStaticParams() {
  return LANGUAGES.map((l) => ({ lang: l.code }));
}

export default async function LanguageLayout({ children, params }: LayoutProps<"/[lang]">) {
  const { lang } = await params;
  if (!isLanguage(lang)) notFound();
  const info = languageInfo(lang);
  return (
    <I18nProvider lang={lang}>
      <header className="mx-auto flex w-full max-w-xl items-center justify-between gap-4 px-4 pt-4">
        <Link href={`/${lang}`} className="text-xl font-semibold">
          Haqqi <span lang="ar">حقّي</span>
        </Link>
        <Link href="/" className="flex min-h-11 items-center gap-2 text-sm text-muted-foreground underline-offset-4 hover:underline">
          <span aria-hidden>{info.flag}</span>
          {translate(lang, "app.changeLanguage")}
        </Link>
      </header>
      <main className="mx-auto flex w-full max-w-xl flex-1 flex-col gap-6 px-4 py-6">{children}</main>
      <footer className="mx-auto w-full max-w-xl px-4 pb-8">
        <Disclaimer lang={lang} />
      </footer>
    </I18nProvider>
  );
}
