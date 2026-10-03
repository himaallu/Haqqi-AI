import { describe, expect, it, vi } from "vitest";

import { LANGUAGES, isLanguage } from "./languages";
import { CATALOGS, translate } from "./translate";

const placeholders = (text: string) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

describe("catalogs", () => {
  const en = CATALOGS.en;

  it.each(LANGUAGES.map((l) => l.code))("%s has exactly the English keys and placeholders", (code) => {
    const catalog = CATALOGS[code];
    expect(Object.keys(catalog).sort()).toEqual(Object.keys(en).sort());
    for (const [key, text] of Object.entries(catalog)) {
      expect(text, `${code}.${key}`).not.toBe("");
      expect(placeholders(text ?? ""), `${code}.${key}`).toEqual(placeholders(en[key as keyof typeof en] ?? ""));
    }
  });

  it("keeps MOHRE's number in every disclaimer and referral contact line", () => {
    for (const catalog of Object.values(CATALOGS)) {
      expect(catalog["disclaimer.text"]).toContain("80084");
      expect(catalog["referral.mohre"]).toContain("80084");
    }
  });
});

describe("languages", () => {
  it("lists the 7 worker languages plus Arabic; Urdu and Arabic are right to left", () => {
    expect(LANGUAGES.map((l) => l.code)).toEqual(["en", "hi", "ur", "ml", "bn", "tl", "ne", "ar"]);
    expect(LANGUAGES.filter((l) => l.dir === "rtl").map((l) => l.code)).toEqual(["ur", "ar"]);
    expect(isLanguage("ur")).toBe(true);
    expect(isLanguage("fr")).toBe(false);
  });
});

describe("translate", () => {
  it("fills placeholders", () => {
    expect(translate("en", "story.count", { count: 12, max: 8000 })).toBe("12 / 8000");
  });

  it("falls back to English and warns when a key is missing", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const saved = CATALOGS.hi["picker.title"];
    delete CATALOGS.hi["picker.title"];
    try {
      expect(translate("hi", "picker.title")).toBe("Choose your language");
      expect(warn).toHaveBeenCalledWith('i18n: missing "picker.title" in hi');
    } finally {
      CATALOGS.hi["picker.title"] = saved;
      warn.mockRestore();
    }
  });
});
