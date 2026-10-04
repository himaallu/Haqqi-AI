"use client";

import { FileDown, Share2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { ApiError, type ComplaintIdentity, downloadComplaint } from "@/lib/api";
import { errorMessageKey } from "@/lib/errors";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n/translate";
import { canShareFile, pdfFile, saveFile, shareFile } from "@/lib/share";

const FILENAME = "haqqi-complaint.pdf";

const FIELDS: { name: keyof ComplaintIdentity; label: MessageKey; maxLength: number }[] = [
  { name: "name", label: "complaint.name", maxLength: 120 },
  { name: "labour_card", label: "complaint.labourCard", maxLength: 40 },
  { name: "employer", label: "complaint.employer", maxLength: 160 },
];

/**
 * Step 7 (task 5.5): the Arabic complaint PDF with a translation alongside. The three identity
 * fields stay in this component's state, go to the backend once, and are never saved (flag 8).
 */
export function ComplaintDownload({ caseId }: { caseId: string }) {
  const { t } = useI18n();
  const [identity, setIdentity] = useState<ComplaintIdentity>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<MessageKey | null>(null);
  // Phones: the PDF waits here for the "Save or share" tap (see lib/share.ts).
  const [ready, setReady] = useState<File | null>(null);

  async function download() {
    setBusy(true);
    setError(null);
    setReady(null);
    try {
      const file = pdfFile(await downloadComplaint(caseId, identity), FILENAME);
      if (canShareFile(file)) setReady(file);
      else saveFile(file);
    } catch (err) {
      setError(err instanceof ApiError && err.status === 409 ? "complaint.unavailable" : errorMessageKey(err));
    } finally {
      setBusy(false);
    }
  }

  async function share(file: File) {
    setError(null);
    try {
      await shareFile(file);
    } catch {
      saveFile(file); // the share sheet was refused: fall back to opening the PDF
    }
  }

  return (
    <section className="flex flex-col gap-4 rounded-lg border p-4" data-testid="complaint">
      <div className="flex flex-col gap-1">
        <h2 className="text-xl font-semibold">{t("complaint.title")}</h2>
        <p className="text-sm text-muted-foreground">{t("complaint.help")}</p>
      </div>
      {FIELDS.map((field) => (
        <div key={field.name} className="flex flex-col gap-1.5">
          <Label htmlFor={`complaint-${field.name}`}>{t(field.label)}</Label>
          <Input
            id={`complaint-${field.name}`}
            autoComplete="off"
            maxLength={field.maxLength}
            value={identity[field.name] ?? ""}
            onChange={(e) => {
              setIdentity({ ...identity, [field.name]: e.target.value });
              setReady(null); // the prepared letter no longer matches the fields
            }}
          />
        </div>
      ))}
      <p className="text-xs text-muted-foreground">{t("complaint.privacy")}</p>
      <Button onClick={download} disabled={busy}>
        <FileDown aria-hidden />
        {busy ? t("complaint.downloading") : t("complaint.download")}
      </Button>
      {ready && (
        <div className="flex flex-col gap-3 rounded-md border bg-muted/40 p-3" data-testid="complaint-ready">
          <p className="font-medium">{t("complaint.ready")}</p>
          <Button onClick={() => share(ready)} data-testid="complaint-share">
            <Share2 aria-hidden />
            {t("complaint.share")}
          </Button>
          <Button variant="outline" onClick={() => saveFile(ready)}>
            {t("complaint.open")}
          </Button>
          <p className="text-xs text-muted-foreground">{t("complaint.saveHint")}</p>
        </div>
      )}
      {error && (
        <p role="alert" className="rounded-md bg-warning-bg px-3 py-2 text-sm text-warning-fg">
          {t(error)}
        </p>
      )}
    </section>
  );
}
