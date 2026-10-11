import { describe, expect, it } from "vitest";
import { HARMLESS, knobLabel, splitKnobs } from "@/lib/settings-knobs";
import { testUi } from "@/tests/fixtures";

describe("settings knobs", () => {
  it("spells out a knob it knows", () => {
    expect(knobLabel("karmacontact", testUi)).toBe("コンタクト 1 点あたりのカルマ");
  });

  it("falls back to the tag for one it does not", () => {
    // a settings file from a newer Chummer than this app was built against
    expect(knobLabel("someknobfromthefuture", testUi)).toBe("someknobfromthefuture");
  });

  it("separates the knobs that can move a number from the ones that cannot", () => {
    const { loud, quiet } = splitKnobs(["essenceformat", "karmaquality"], testUi);
    expect(loud).toEqual(["資質 1 点あたりのカルマ"]);
    expect(quiet).toEqual(["エッセンスの小数桁数（Chummer の表示設定）"]);
  });

  it("treats an unknown tag as one that matters", () => {
    // the safe side: a house rule nobody was told about is the failure here
    const { loud, quiet } = splitKnobs(["someknobfromthefuture"], testUi);
    expect(loud).toEqual(["someknobfromthefuture"]);
    expect(quiet).toEqual([]);
  });

  it("has a sentence for every knob it calls harmless", () => {
    for (const tag of HARMLESS) expect(knobLabel(tag, testUi), tag).not.toBe(tag);
  });
});
