import { expect, it, describe } from "vitest";
import { buildMethodLabel, priorityCellLabel } from "@/lib/character/priority-labels";
import { translate } from "@/lib/i18n";

const ja = (k: Parameters<typeof translate>[1], v?: Record<string, string | number>) =>
  translate("ja", k, v);
const en = (k: Parameters<typeof translate>[1], v?: Record<string, string | number>) =>
  translate("en", k, v);

describe("priorityCellLabel", () => {
  it("names the metatype rows", () => {
    expect(priorityCellLabel("Any metatype", ja)).toBe("全てのメタタイプ");
    expect(priorityCellLabel("Human, Dwarf, Elf, Ork, or A.I.", ja)).toBe(
      "ドワーフ, オーク, エルフ, ヒューマン, or A.I.",
    );
    expect(priorityCellLabel("Human or Elf", ja)).toBe("エルフ or ヒューマン");
    expect(priorityCellLabel("Human", ja)).toBe("ヒューマン");
  });

  it("names the talent rows", () => {
    expect(priorityCellLabel("Magician or Technomancer", ja)).toBe("魔法使い or テクノマンサー");
    expect(priorityCellLabel("Adept, Magician, or Technomancer", ja)).toBe(
      "アデプト, 魔法使い or テクノマンサー",
    );
    expect(priorityCellLabel("Adept or Aspected Magician", ja)).toBe("アデプト or 偏位魔法使い");
  });

  it("rewrites the number-bearing rows by shape, keeping both numbers", () => {
    expect(priorityCellLabel("24 (12) Attributes", ja)).toBe("24 (12) 能力値");
    expect(priorityCellLabel("12 (6) Attributes", ja)).toBe("12 (6) 能力値");
    expect(priorityCellLabel("46 Skills/10 Skill Groups", ja)).toBe("46 技能/10 技能グループ");
    expect(priorityCellLabel("22 Skills/0 Skill Groups", ja)).toBe("22 技能/0 技能グループ");
  });

  it("passes through what it does not recognise", () => {
    // resource rows are already language-neutral, and a house-ruled row must
    // still render rather than disappear
    expect(priorityCellLabel("450,000¥", ja)).toBe("450,000¥");
    expect(priorityCellLabel("Something homebrewed", ja)).toBe("Something homebrewed");
  });

  it("round-trips to the original English in the en locale", () => {
    for (const name of [
      "Any metatype",
      "Human, Dwarf, Elf, Ork, or A.I.",
      "Human or Elf",
      "Human",
      "Magician or Technomancer",
      "Adept, Magician, or Technomancer",
      "Adept or Aspected Magician",
      "24 (12) Attributes",
      "46 Skills/10 Skill Groups",
    ]) {
      expect(priorityCellLabel(name, en)).toBe(name);
    }
  });
});

describe("buildMethodLabel", () => {
  it("translates Priority and keeps the other two as they read on the sheet", () => {
    expect(buildMethodLabel("Priority", ja)).toBe("優先度");
    expect(buildMethodLabel(undefined, ja)).toBe("優先度");
    expect(buildMethodLabel("SumToTen", ja)).toBe("Sum to Ten");
    expect(buildMethodLabel("Karma", ja)).toBe("Karma");
    expect(buildMethodLabel("Priority", en)).toBe("Priority");
  });
});
