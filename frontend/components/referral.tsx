"use client";

import Link from "next/link";

import { MohreCall } from "@/components/mohre-call";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n/translate";
import type { Referral as ReferralKind } from "@/lib/types";

const TEXTS: Record<ReferralKind, MessageKey> = {
  domestic: "referral.domestic",
  difc_adgm: "referral.difc_adgm",
  free_zone: "referral.free_zone",
};

/** Task 4.7: out-of-scope cases get a referral instead of a verdict (flag 1). */
export function Referral({ kind }: { kind: ReferralKind | null }) {
  const { lang, t } = useI18n();
  return (
    <section className="flex flex-col gap-4" data-testid="referral" data-kind={kind ?? ""}>
      <h1 className="text-2xl font-semibold">{t("referral.title")}</h1>
      {kind && <p className="text-lg">{t(TEXTS[kind])}</p>}
      <p className="rounded-md border px-4 py-3 font-medium">{t("referral.mohre")}</p>
      <MohreCall />
      <Button asChild variant="outline">
        <Link href={`/${lang}`}>{t("common.startOver")}</Link>
      </Button>
    </section>
  );
}
