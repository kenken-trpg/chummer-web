import { describe, expect, it } from "vitest";
import { formatMessage, translate, LOCALES, MESSAGES } from "@/lib/i18n/messages";
import type { Locale, MsgKey } from "@/lib/i18n/messages";

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
    for (const [key, value] of Object.entries(MESSAGES[locale])) {
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
        expect(placeholders(MESSAGES[locale][key]), `${locale} ${key}`).toEqual(want);
      }
    }
  });
});

describe("formatMessage", () => {
  it("leaves unknown placeholders untouched", () => {
    expect(formatMessage("hi {name} {x}", { name: "Jo" })).toBe("hi Jo {x}");
  });
});
