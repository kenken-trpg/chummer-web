import { beforeAll, describe, expect, it, vi } from "vitest";
import { formatMessage, loadLocale, translate, LOCALES, MESSAGES } from "@/lib/i18n/messages";
import type { Catalog, Locale, MsgKey } from "@/lib/i18n/messages";

/** Only `ja` is in the bundle; everything that compares locales has to fetch
 *  the others first, which is what the app does on a locale switch. */
beforeAll(async () => {
  await Promise.all(LOCALES.map((l) => loadLocale(l)));
});

/** A locale known to be here, for the comparisons below. */
const catalog = (locale: Locale): Catalog => {
  const c = MESSAGES[locale];
  if (!c) throw new Error(`${locale} was not loaded`);
  return c;
};

describe("lazy catalogs", () => {
  it("ships only ja, and answers in ja until another arrives", async () => {
    // a fresh module registry, because `beforeAll` has already loaded `en`
    // into this one: the whole point is what happens before that
    vi.resetModules();
    const m = await import("@/lib/i18n/messages");
    expect(m.catalogLoaded("ja")).toBe(true);
    expect(m.catalogLoaded("en")).toBe(false);
    expect(m.translate("en", "tab.priority")).toBe("優先度");

    await m.loadLocale("en");

    expect(m.catalogLoaded("en")).toBe(true);
    expect(m.translate("en", "tab.priority")).toBe("Priority");
  });

  it("hands back the same catalog object on a second load", async () => {
    expect(await loadLocale("en")).toBe(await loadLocale("en"));
  });
});

describe("translate", () => {
  it("returns the requested locale's string", () => {
    expect(translate("en", "tab.priority")).toBe("Priority");
    expect(translate("ja", "tab.priority")).toBe("優先度");
  });

  it("falls back to ja for a locale that is not one of ours", () => {
    // only reachable through a stale localStorage value or a cast
    expect(translate("de" as Locale, "tab.priority")).toBe("優先度");
  });

  it("returns the key itself for an unknown key", () => {
    expect(translate("en", "nope.nope" as MsgKey)).toBe("nope.nope");
  });

  it("interpolates named placeholders", () => {
    expect(translate("en", "check.summary", { errors: 1, warns: 2, infos: 3 })).toBe(
      "1 errors · 2 warnings · 3 notes",
    );
  });
});

describe("catalogs", () => {
  // `Record<MsgKey, string>` already forces every locale to define every key;
  // what it cannot catch is a key defined as "" (or as the ja text pasted into
  // `en` unchanged for a message that should differ).
  it.each(LOCALES)("%s has a non-empty string for every key", (locale) => {
    for (const [key, value] of Object.entries(catalog(locale))) {
      expect(value.trim(), `${locale} ${key}`).not.toBe("");
    }
  });

  it("keeps the same placeholders in every locale", () => {
    const placeholders = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const key of Object.keys(MESSAGES.ja) as MsgKey[]) {
      const want = placeholders(MESSAGES.ja[key]);
      for (const locale of LOCALES) {
        // a translation that drops `{length}` silently renders a sentence with
        // a hole in it, and nothing else would notice
        expect(placeholders(catalog(locale)[key]), `${locale} ${key}`).toEqual(want);
      }
    }
  });
});

describe("formatMessage", () => {
  it("leaves unknown placeholders untouched", () => {
    expect(formatMessage("hi {name} {x}", { name: "Jo" })).toBe("hi Jo {x}");
  });
});
