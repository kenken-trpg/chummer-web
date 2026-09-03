import { describe, expect, it } from "vitest";
import { formatMessage, translate } from "@/lib/i18n/messages";
import type { MsgKey } from "@/lib/i18n/messages";

describe("translate", () => {
  it("returns the requested locale's string", () => {
    expect(translate("en", "tab.priority")).toBe("Priority");
    expect(translate("ja", "tab.priority")).toBe("優先度");
  });

  it("falls back to ja when the en string is missing", () => {
    // "locale.ja" has no `en` entry on purpose.
    expect(translate("en", "locale.ja")).toBe("日本語");
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

describe("formatMessage", () => {
  it("leaves unknown placeholders untouched", () => {
    expect(formatMessage("hi {name} {x}", { name: "Jo" })).toBe("hi Jo {x}");
  });
});
