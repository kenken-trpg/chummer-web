import { render } from "@testing-library/react";
import { buildSheetData } from "@/lib/character/sheet-data";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";
import { ActionDpSection } from "@/components/character/sheet/sections/ActionDp";
import { CareerSection } from "@/components/character/sheet/sections/Career";
import { CombatSection } from "@/components/character/sheet/sections/Combat";
import { ContactsSection } from "@/components/character/sheet/sections/Contacts";
import { CoreSection } from "@/components/character/sheet/sections/Core";
import { DescriptionSection } from "@/components/character/sheet/sections/Description";
import { DrugsSection } from "@/components/character/sheet/sections/Drugs";
import { KnowledgeSection } from "@/components/character/sheet/sections/Knowledge";
import { MagicSection } from "@/components/character/sheet/sections/Magic";
import { MartialSection } from "@/components/character/sheet/sections/Martial";
import { MatrixSection } from "@/components/character/sheet/sections/Matrix";
import { MiscGearSection } from "@/components/character/sheet/sections/MiscGear";
import { QualitiesSection } from "@/components/character/sheet/sections/Qualities";
import { ResonanceSection } from "@/components/character/sheet/sections/Resonance";
import { SinSection } from "@/components/character/sheet/sections/Sin";
import { SkillsSection } from "@/components/character/sheet/sections/Skills";
import { VehiclesSection } from "@/components/character/sheet/sections/Vehicles";
import { WareSection } from "@/components/character/sheet/sections/Ware";

/* eslint-disable @typescript-eslint/no-explicit-any */

// A `derived` payload that touches every sheet section with realistic nested
// rows. Rows are hand-shaped only far enough to render, then cast — like the
// rest of the suite's fixtures.
const RICH_DERIVED = {
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
  armor_items: [{ id: "a1", name: "Armor Jacket", armor: 12, mods: [] }],
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

// One character that touches every sheet section with realistic nested rows.
// The point is a shallow guard: each section renders (no throw) and shows its
// heading once its slice of `derived` is populated — so a nested-shape change
// in the payload surfaces here instead of at runtime. (Top-level key parity is
// pinned server-side by backend/tests/test_derived_contract.py.)
const CHARACTER = makeCharacter({
  notes: "背景メモ",
  skills: { Pistols: 4 },
  derived: RICH_DERIVED,
});

const CATALOG = makeCatalog({
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

const s = buildSheetData({
  character: CHARACTER,
  catalog: CATALOG,
  tr: identityTr,
  layout: "standard",
});

const SECTIONS: [string, (p: typeof s) => React.ReactNode, string][] = [
  ["コア", CoreSection, "イニシアチブ"],
  ["技能", SkillsSection, "Pistols"],
  ["知識技能", KnowledgeSection, "Seattle Gangs"],
  ["キャリア", CareerSection, "報酬"],
  ["資質", QualitiesSection, "Ambidextrous"],
  ["アクションDP", ActionDpSection, "Hack"],
  ["戦闘", CombatSection, "Ares Predator V"],
  ["ウェア", WareSection, "Wired Reflexes"],
  ["マトリクス", MatrixSection, "Meta Link"],
  ["魔法", MagicSection, "Manabolt"],
  ["共鳴", ResonanceSection, "Cleaner"],
  ["武道", MartialSection, "Krav Maga"],
  ["コンタクト", ContactsSection, "Fixer"],
  ["車両・ドローン", VehiclesSection, "Ford Americar"],
  ["ドラッグ／毒物", DrugsSection, "Kamikaze"],
  ["SIN／ライセンス", SinSection, "Fake SIN"],
  ["その他ギア", MiscGearSection, "Medkit"],
  ["記述", DescriptionSection, "背景メモ"],
];

describe("sheet sections — smoke render", () => {
  it.each(SECTIONS)("%s renders with populated derived data", (_title, Section, marker) => {
    const { container } = render(<Section {...(s as any)} />);
    // the section did not collapse to null and shows a representative value
    expect(container.querySelector("section.sheet-section")).not.toBeNull();
    expect(container.textContent).toContain(marker);
  });

  it("every section collapses to null for an empty character", () => {
    const empty = buildSheetData({
      character: makeCharacter(),
      catalog: makeCatalog(),
      tr: identityTr,
      layout: "standard",
    });
    for (const [title, Section] of SECTIONS) {
      if (title === "コア") continue; // always-on
      const { container } = render(<Section {...(empty as any)} />);
      expect(container.querySelector("section.sheet-section")).toBeNull();
    }
  });
});
