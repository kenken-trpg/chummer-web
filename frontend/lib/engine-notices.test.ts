import { describe, expect, it } from "vitest";
import { renderNotice, vehicleSlotLabel } from "@/lib/engine-notices";
import { translate } from "@/lib/i18n";
import type { Locale, MsgKey } from "@/lib/i18n";

const uiFor =
  (locale: Locale) =>
  (key: MsgKey, vars?: Record<string, string | number>): string =>
    translate(locale, key, vars);

/** Stand-in for `makeTr`: the catalog table is English -> Japanese. */
const tr = (name: string) => ({ "Ares Predator V": "アレス・プレデターV" })[name] ?? name;

describe("renderNotice", () => {
  it("renders an engine notice in each locale", () => {
    const notice = {
      key: "engine.skills.pointsOver",
      params: { used: 5, max: 4 },
    };
    expect(renderNotice(notice, uiFor("ja"))).toBe("技能点が不足しています（使用 5 / 上限 4）");
    expect(renderNotice(notice, uiFor("en"))).toBe("Not enough skill points (spent 5 / 4)");
  });

  it("translates a catalog name, so the Japanese sentence reads in Japanese", () => {
    const notice = {
      key: "engine.gear.availOver",
      params: { name: { tr: "Ares Predator V" }, shown: "9R", limit: 12 },
    };
    expect(renderNotice(notice, uiFor("ja"), tr)).toContain("アレス・プレデターV");
    // `tr` is the identity in English — the catalog is English to begin with
    expect(renderNotice(notice, uiFor("en"), (n) => n)).toContain("Ares Predator V");
  });

  it("looks up a phrase parameter as a key of its own", () => {
    const notice = {
      key: "engine.ware.sideDuplicate",
      params: { side: { ui: "engine.side.Left" }, slot: { ui: "engine.slot.arm" } },
    };
    expect(renderNotice(notice, uiFor("ja"))).toBe("左の腕が重複しています");
    expect(renderNotice(notice, uiFor("en"))).toBe("Duplicate left arm");
  });

  it("joins a list parameter", () => {
    const notice = {
      key: "engine.ware.requires",
      params: {
        name: { tr: "Orthoskin Upgrade" },
        needed: [{ tr: "Orthoskin" }, { tr: "Bone Density" }],
      },
    };
    expect(renderNotice(notice, uiFor("en"), (n) => n)).toBe(
      "Orthoskin Upgrade requires Orthoskin / Bone Density",
    );
  });

  it("shows an unknown key as itself rather than blanking the line", () => {
    // an engine deployed ahead of the front end: visible, not silent
    expect(renderNotice({ key: "engine.future.rule" }, uiFor("ja"))).toBe("engine.future.rule");
  });
});

describe("vehicleSlotLabel", () => {
  it("names a known slot category and passes an unknown one through", () => {
    expect(vehicleSlotLabel("Powertrain", uiFor("ja"))).toBe("パワートレイン");
    expect(vehicleSlotLabel("Powertrain", uiFor("en"))).toBe("powertrain");
    expect(vehicleSlotLabel("Nanotech", uiFor("en"))).toBe("Nanotech");
  });
});
