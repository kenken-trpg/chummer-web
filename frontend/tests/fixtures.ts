import type { Catalog, Character } from "@/lib/types";

/** Identity translator — tests assert on English names, not the JA overlay. */
export const identityTr = (name: string) => name;

type Derived = Character["derived"];

function makeDerived(overrides: Partial<Derived> = {}): Derived {
  return {
    errors: [],
    totals: { BOD: 3, AGI: 3, REA: 3, STR: 3, CHA: 3, INT: 3, LOG: 3, WIL: 3, EDG: 3 },
    limits: { physical: 3, mental: 4, social: 4 },
    condition_monitor: { physical: 10, stun: 10 },
    initiative: { value: 6, dice: 1 },
    movement: { walk: "2/1/0", run: "4/0/0", sprint: "2/1/0" },
    essence: 6,
    armor: 0,
    nuyen: 0,
    karma: { pool: 25, spent: 0, remaining: 25 },
    points: {
      attributes: { used: 0, max: 0 },
      special: { used: 0, max: 0 },
      skills: { used: 0, max: 0 },
      knowledge: { used: 0, max: 0 },
    },
    skill_totals: {},
    enabled_tabs: [],
    unimplemented_bonuses: [],
    qualities: [],
    cyberware: [],
    metatype_info: { name: "Human", attributes: {} },
    ...overrides,
  };
}

/** A fully-typed minimal Character: an empty Human runner with a complete
 * `derived` (every required nested object present, arrays empty). Pass
 * `overrides` / `derived` to populate specific sections. */
export function makeCharacter(
  overrides: Partial<Omit<Character, "derived">> & { derived?: Partial<Derived> } = {},
): Character {
  const { derived, ...rest } = overrides;
  return {
    id: "test-char",
    name: "Test Runner",
    priorities: { Heritage: "E", Attributes: "C", Talent: "E", Skills: "B", Resources: "D" },
    metatype: "Human",
    metavariant: null,
    talent: "Mundane",
    attributes: { BOD: 3, AGI: 3, REA: 3, STR: 3, CHA: 3, INT: 3, LOG: 3, WIL: 3, EDG: 3 },
    skills: {},
    skill_groups: {},
    knowledge_skills: {},
    quality_ids: [],
    cyberware: [],
    ...rest,
    derived: makeDerived(derived),
  };
}

/** Minimal catalog covering only what `buildSheetData` / `CharacterSheet`
 * read: `skills.{skills,groups}`, `weapon_ranges`, `ui_strings`. */
export function makeCatalog(overrides: Partial<Catalog> = {}): Catalog {
  return {
    skills: { skills: [], groups: [] },
    qualities: [],
    weapon_ranges: {},
    ui_strings: {},
    ...overrides,
  } as Catalog;
}
