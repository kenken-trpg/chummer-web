import type { Catalog, Character } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";
import { translate } from "@/lib/i18n/messages";

/** Identity translator — tests assert on English names, not the JA overlay. */
export const identityTr = (name: string) => name;

/**
 * The real `ui()`, pinned to `ja`.
 *
 * Not a stub returning the key: the tabs render app copy through this, and the
 * assertions in these tests are the user-visible wording. Pinning the locale
 * keeps them independent of whatever `localStorage` a previous test left
 * behind — a test that wants English sets the locale itself.
 */
export const testUi: UiFn = (key, vars) => translate("ja", key, vars);

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
      skill_groups: { used: 0, max: 0 },
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
 * read: `skills.{skills,groups}`, `weapon_ranges`, `ui_strings`. Every
 * catalog collection a tab might `.map()` / `.filter()` is present and empty,
 * so any tab renders against a bare `makeCatalog()`; pass `overrides` for the
 * specific slice under test. */
export function makeCatalog(overrides: Partial<Catalog> = {}): Catalog {
  const emptyWare = { items: [], grades: [] };
  return {
    skills: { skills: [], groups: [], knowledge: [] },
    qualities: [],
    metatypes: [],
    priority_table: {},
    translations: {},
    ui_strings: {},
    weapon_ranges: {},
    cyberware: emptyWare,
    bioware: emptyWare,
    powers: [],
    enhancements: [],
    mentors: [],
    spells: [],
    traditions: [],
    spirits: [],
    complex_forms: [],
    streams: [],
    sprites: [],
    foci: [],
    qi_focus: null,
    armor: [],
    armor_mods: [],
    weapons: [],
    weapon_accessories: [],
    commlinks: [],
    cyberdecks: [],
    rccs: [],
    optics: [],
    programs: [],
    apps: [],
    sensors: [],
    gear: [],
    drones: [],
    vehicles: [],
    vehicle_mods: [],
    weapon_mounts: [],
    ...overrides,
  } as Catalog;
}

/**
 * A `derived` payload that touches every sheet section with realistic nested
 * rows. Rows are hand-shaped only far enough to render, then cast — like the
 * rest of these fixtures.
 *
 * Shared by the sheet-section smoke render and the text sheet: both consume
 * the same `buildSheetData()` bag, so a payload shaped for one has to be the
 * one the other sees, or the two drift and only one of them notices.
 */
export const RICH_DERIVED = {
  enabled_tabs: ["magic", "spells", "adept", "complexforms", "sprites", "submersion"],
  skill_totals: { Pistols: 4 },
  unarmed_dv: 3,
  unarmed_ap: 1,
  limit_modifiers: [{ limit: "physical", value: 1, condition: "", source: "Reflex Recorder" }],
  weapons: [
    {
      id: "w1",
      name: "Ares Predator V",
      category: "Heavy Pistols",
      type: "Ranged",
      useskill: "Pistols",
      damage: "8P",
      ap: "-1",
      accuracy: "5",
      mode: "SA",
      qty: 1,
      accessories: [],
    },
  ],
  // `equipped` matters: buildSheetData drops armor that is neither equipped
  // nor contributing, so without it this row is silently invisible to every
  // consumer of the fixture.
  armor_items: [{ id: "a1", name: "Armor Jacket", armor: 12, equipped: true, mods: [] }],
  action_dice_pools: [{ category: "Matrix", name: "Hack", bonus: 2, source: "Codeslinger" }],
  adept_powers: [{ id: "ap1", name: "Improved Reflexes", rating: 2, pp: 2.5 }],
  power_points: { used: 2.5, max: 6 },
  foci: [{ id: "f1", name: "Power Focus", force: 2, bonded: true }],
  qi_foci: [],
  spirits: [{ id: "sp1", name: "Spirit of Fire", force: 3, services: 2 }],
  spells: [
    {
      id: "s1",
      name: "Manabolt",
      category: "Combat",
      type: "M",
      range: "LOS",
      duration: "I",
      dv: "F-3",
    },
  ],
  drain_resist: { pool: 6, attrs: "WIL+LOG" },
  initiation: { grade: 1, karma: 13, choices: [], metamagics: [], arts: [] },
  complex_forms: [
    {
      id: "cf1",
      name: "Cleaner",
      label: "Cleaner",
      target: "Persona",
      duration: "P",
      level: 3,
      fv: "L-2",
    },
  ],
  sprites: [{ id: "spr1", name: "Courier Sprite", level: 3, services: 2 }],
  fade_resist: { pool: 6, attrs: "WIL+RES" },
  submersion: { grade: 1, karma: 13, choices: [], echoes: [] },
  living_persona: { attack: 4, sleaze: 3, dataprocessing: 3, firewall: 2 },
  commlink: {
    id: "cl1",
    name: "Meta Link",
    rating: 1,
    attack: 0,
    sleaze: 0,
    dataprocessing: 1,
    firewall: 1,
  },
  cyberware: [{ id: "c1", name: "Wired Reflexes", rating: 2, essence: 2 }],
  bioware: [{ id: "b1", name: "Muscle Toner", rating: 2, essence: 0.4 }],
  essence_lost_cyber: 2,
  essence_lost_bio: 0.4,
  vehicles: [
    {
      id: "v1",
      name: "Ford Americar",
      category: "Cars",
      handling: "4",
      speed: "3",
      accel: "2",
      body: "11",
      armor: "6",
      pilot: "1",
      sensor: "2",
      nuyen: 16000,
      mods: [],
      weapon_mounts: [],
      sensors: [],
      gear: [],
    },
  ],
  drones: [],
  knowledge_skills: [
    { name: "Seattle Gangs", category: "Street", attribute: "INT", rating: 3, native: false },
  ],
  martial_arts: [
    {
      id: "m1",
      art_id: "a1",
      name: "Krav Maga",
      karma: 7,
      style_karma: 7,
      techniques: [],
      technique_options: [],
    },
  ],
  contacts: [
    {
      id: "ct1",
      name: "Fixer",
      role: "情報屋",
      connection: 3,
      loyalty: 2,
      connection_max: 6,
      loyalty_max: 6,
    },
  ],
  active_drugs: [{ name: "Kamikaze", effect: "+1 BOD/AGI/STR/WIL", duration: "10分" }],
  gear: [
    { id: "g1", name: "Medkit", rating: 6, qty: 1 },
    { id: "dr1", name: "Novacoke", category: "Drugs", qty: 2 },
    { id: "sin1", name: "Fake SIN (R4)", category: "ID/Credsticks", rating: 4, qty: 1 },
  ],
  career: true,
  karma_earned: 20,
  nuyen_earned: 5000,
  street_cred: 2,
  notoriety: 1,
  public_awareness: 0,
  career_advancement_karma: 4,
  reward_log: [{ id: "r1", label: "Milk run", karma: 5, nuyen: 4000 }],
  karma_spend_breakdown: [{ label: "資質", amount: 4 }],
  nuyen_spend_breakdown: [{ label: "ギア", amount: 1000 }],
  qualities: [{ id: "q1", name: "Ambidextrous", karma: 4, category: "Positive", source: "SR5" }],
} as any;

export const RICH_CHARACTER = makeCharacter({
  notes: "背景メモ",
  skills: { Pistols: 4 },
  derived: RICH_DERIVED,
});

export const RICH_CATALOG = makeCatalog({
  skills: {
    groups: [],
    skills: [
      {
        name: "Pistols",
        attribute: "AGI",
        category: "Combat Active",
        exotic: false,
        source: "SR5",
      },
    ],
  } as any,
});
