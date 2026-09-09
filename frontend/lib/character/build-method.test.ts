import { describe, expect, it } from "vitest";
import { buildMethodPatch } from "@/lib/character/build-method";
import type { Character } from "@/lib/types";

function ch(letters: Partial<Character["priorities"]>, talent = "Magician"): Character {
  return {
    priorities: {
      Heritage: "C",
      Attributes: "A",
      Talent: "E",
      Skills: "B",
      Resources: "D",
      ...letters,
    },
    talent,
  } as Character;
}

describe("buildMethodPatch", () => {
  it("keeps a Priority-legal spread when switching to Priority", () => {
    expect(buildMethodPatch("Priority", ch({}))).toEqual({ build_method: "Priority" });
  });

  it("resets a spread that is not a permutation of A-E", () => {
    // Sum-to-Ten allows duplicates; carrying those into Priority would leave
    // the character on a table it can never satisfy
    expect(buildMethodPatch("Priority", ch({ Skills: "A" }))).toEqual({
      build_method: "Priority",
      priorities: { Heritage: "C", Attributes: "A", Talent: "E", Skills: "B", Resources: "D" },
      talent: "Mundane",
    });
  });

  it("carries the talent into Karma, defaulting to Mundane", () => {
    expect(buildMethodPatch("Karma", ch({}))).toEqual({
      build_method: "Karma",
      talent: "Magician",
    });
    expect(buildMethodPatch("Karma", ch({}, ""))).toEqual({
      build_method: "Karma",
      talent: "Mundane",
    });
  });

  it("changes nothing else for Sum-to-Ten", () => {
    expect(buildMethodPatch("SumToTen", ch({ Skills: "A" }))).toEqual({
      build_method: "SumToTen",
    });
  });
});
