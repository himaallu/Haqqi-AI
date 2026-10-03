"use client";

import { Mic } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Label, Textarea } from "@/components/ui/field";
import { createCase } from "@/lib/api";
import { errorMessageKey } from "@/lib/errors";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n/translate";

export const MAX_STORY_CHARS = 8000; // backend/haqqi/api/schemas.py

/** Step 2 (task 4.3): the worker tells their story; the Intake agent reads it and the confirm step follows. */
export function StoryForm() {
  const { lang, t } = useI18n();
  const router = useRouter();
  const [story, setStory] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<MessageKey | null>(null);

  const tooLong = story.length > MAX_STORY_CHARS;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!story.trim() || tooLong || busy) return;
    setBusy(true);
    setError(null);
    try {
      const view = await createCase({ language: lang, story });
      router.push(`/${lang}/case/${view.id}`);
    } catch (err) {
      setError(errorMessageKey(err));
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">{t("story.title")}</h1>
        <p className="text-muted-foreground">{t("story.help")}</p>
      </div>

      <p role="note" className="rounded-md bg-warning-bg px-3 py-2 text-sm text-warning-fg">
        {t("story.privacy")}
      </p>

      <div className="flex flex-col gap-2">
        <Label htmlFor="story" className="sr-only">
          {t("story.title")}
        </Label>
        <Textarea
          id="story"
          name="story"
          value={story}
          onChange={(e) => setStory(e.target.value)}
          placeholder={t("story.placeholder")}
          aria-invalid={tooLong || undefined}
          aria-describedby="story-count"
          rows={8}
          required
          disabled={busy}
        />
        <div className="flex items-center justify-between gap-2 text-sm">
          <Button type="button" variant="outline" size="sm" disabled title={t("story.mic")}>
            <Mic aria-hidden className="size-4" />
            {t("story.mic")}
          </Button>
          <span id="story-count" className={tooLong ? "text-destructive" : "text-muted-foreground"}>
            {t("story.count", { count: story.length, max: MAX_STORY_CHARS })}
          </span>
        </div>
        {tooLong && <p className="text-sm text-destructive">{t("story.tooLong", { max: MAX_STORY_CHARS })}</p>}
      </div>

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {t(error)}
        </p>
      )}

      <Button type="submit" size="lg" disabled={busy || !story.trim() || tooLong}>
        {busy ? t("story.submitting") : t("story.submit")}
      </Button>
      <p className="text-xs text-muted-foreground">{t("story.processing")}</p>
    </form>
  );
}
