import { skillDefault } from "@/lib/character/skill-default";
import { makeCharacter } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const pistols = { name: "Pistols", attribute: "AGI", category: "Combat Active" };

const derived = (over: Record<string, unknown> = {}) =>
  makeCharacter({ derived: { totals: { AGI: 5, INT: 3 }, ...over } } as any).derived;

describe("skillDefault", () => {
  it("rolls the linked attribute minus one", () => {
    expect(skillDefault(pistols, derived())).toEqual({
      blocked: false,
      pool: 4,
      free: false,
      attribute: "AGI",
    });
  });

  it("counts a dice bonus the skill already carries", () => {
    const d = derived({ skill_bonus: { Pistols: 2 } });
    expect(skillDefault(pistols, d)).toMatchObject({ pool: 6 });
  });

  it("keeps the whole attribute for a skill the recorder covers", () => {
    const d = derived({ no_default_penalty_skills: ["Pistols"] });
    expect(skillDefault(pistols, d)).toMatchObject({ pool: 5, free: true });
  });

  it("never goes below zero dice", () => {
    const d = derived({ totals: { AGI: 0 } });
    expect(skillDefault(pistols, d)).toMatchObject({ pool: 0 });
  });

  it("says so when the skill itself cannot be defaulted", () => {
    expect(skillDefault({ ...pistols, default: false }, derived())).toEqual({ blocked: true });
  });

  it("says so when something blocked the whole category", () => {
    const d = derived({ blocked_default_categories: ["Combat Active"] });
    expect(skillDefault(pistols, d)).toEqual({ blocked: true });
  });
});
