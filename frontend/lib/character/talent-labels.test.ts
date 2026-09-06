import { expect, it, describe } from "vitest";
import { talentLabel } from "@/lib/character/talent-labels";
import { translate } from "@/lib/i18n";

const ja = (k: Parameters<typeof translate>[1], v?: Record<string, string | number>) =>
  translate("ja", k, v);
const en = (k: Parameters<typeof translate>[1], v?: Record<string, string | number>) =>
  translate("en", k, v);

describe("talentLabel", () => {
  it("translates the name and the ratings tail separately", () => {
    expect(talentLabel("Magician", "Magician - 6 Magic/10 Spells", ja)).toBe(
      "魔法使い - 魔力6/術式10",
    );
    expect(talentLabel("Mystic Adept", "Mystic Adept - 3 Magic/5 Spells", ja)).toBe(
      "ミスティックアデプト - 魔力3/術式5",
    );
    expect(talentLabel("Adept", "Adept - 6 Magic", ja)).toBe("アデプト - 魔力6");
    expect(talentLabel("Aspected Magician", "Aspected Magician - 2 Magic", ja)).toBe(
      "偏位魔法使い - 魔力2",
    );
    expect(talentLabel("Technomancer", "Technomancer - 4 Resonance/4 Complex Forms", ja)).toBe(
      "テクノマンサー - 共振力4/複合体4",
    );
  });

  it("handles the tail-less options", () => {
    expect(talentLabel("Mundane", "Mundane", ja)).toBe("マンディン");
    expect(talentLabel("Mundane", undefined, ja)).toBe("マンディン");
  });

  it("leaves Run Faster's talents under their English names, tail translated", () => {
    // as the Run Faster metavariants are — the katakana would be a
    // transliteration rather than an established Japanese form
    expect(talentLabel("Apprentice", "Apprentice - 5 Magic", ja)).toBe("Apprentice - 魔力5");
    expect(talentLabel("Aware", "Aware - 3 Magic", ja)).toBe("Aware - 魔力3");
    expect(talentLabel("Enchanter", "Enchanter - 5 Magic", ja)).toBe("Enchanter - 魔力5");
    expect(talentLabel("Explorer", "Explorer - 5 Magic", ja)).toBe("Explorer - 魔力5");
  });

  it("passes an unrecognised shape through untouched", () => {
    expect(talentLabel("Houseruled", "Houseruled - 9 Vibes", ja)).toBe("Houseruled - 9 Vibes");
    // a label that is not built from the name at all is left exactly as it came
    expect(talentLabel("Adept", "Something else entirely", ja)).toBe("Something else entirely");
  });

  it("round-trips to the shipped English in the en locale", () => {
    for (const [name, label] of [
      ["Magician", "Magician - 6 Magic/10 Spells"],
      ["Adept", "Adept - 4 Magic"],
      ["Technomancer", "Technomancer - 6 Resonance/7 Complex Forms"],
      ["Mundane", "Mundane"],
    ] as const) {
      expect(talentLabel(name, label, en)).toBe(label);
    }
  });
});
