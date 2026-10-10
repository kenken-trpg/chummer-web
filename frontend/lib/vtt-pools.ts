/**
 * The parts of a dice pool that every VTT export needs, whatever shape it
 * writes them in.
 *
 * Cocofolia (`cocofolia.ts`) and Udonarium (`udonarium.ts`) ask the same three
 * questions — which limit an attribute caps a test at, which skill a weapon is
 * fired with, and which attribute a skill is rolled off — and they have to get
 * the same answers, or the two exports of one character disagree.
 */
import type { Catalog, Derived } from "@/lib/types";

export type LimitKind = "physical" | "mental" | "social" | null;

export const ATTR_LIMIT: Record<string, LimitKind> = {
  BOD: "physical",
  AGI: "physical",
  REA: "physical",
  STR: "physical",
  CHA: "social",
  INT: "mental",
  LOG: "mental",
  WIL: "mental",
  EDG: null,
  MAG: null,
  RES: null,
};

// weapon category -> active skill (Chummer Weapon.GetSkillDictionaryKey, trimmed)
const WEAPON_SKILL: Record<string, string> = {
  Bows: "Archery",
  Crossbows: "Archery",
  "Assault Rifles": "Automatics",
  Carbines: "Automatics",
  "Machine Pistols": "Automatics",
  "Submachine Guns": "Automatics",
  Blades: "Blades",
  Clubs: "Clubs",
  "Improvised Weapons": "Clubs",
  "Assault Cannons": "Heavy Weapons",
  "Grenade Launchers": "Heavy Weapons",
  "Missile Launchers": "Heavy Weapons",
  "Light Machine Guns": "Heavy Weapons",
  "Medium Machine Guns": "Heavy Weapons",
  "Heavy Machine Guns": "Heavy Weapons",
  Shotguns: "Longarms",
  "Sniper Rifles": "Longarms",
  "Sporting Rifles": "Longarms",
  "Throwing Weapons": "Throwing Weapons",
  Unarmed: "Unarmed Combat",
};

export const weaponSkill = (w: { useskill?: string; category?: string }) =>
  (w.useskill || "").trim() || WEAPON_SKILL[w.category || ""] || "Pistols";

/**
 * Which attribute each skill is rolled off, and the swaps that move one.
 *
 * `<swapskillattribute>` (Empathic Listener: Etiquette off INT) moves the pool
 * *and* the limit that comes with the attribute, so it is folded into
 * `skillAttr`. The spec-limited variant only moves the specialized roll, so it
 * stays in `specSwap` for the caller to apply to that roll alone.
 */
export function skillAttributes(catalog: Catalog, d: Derived) {
  const skillAttr: Record<string, string> = {};
  for (const s of catalog.skills?.skills || []) skillAttr[s.name] = s.attribute;
  for (const s of d.exotic_skills || []) skillAttr[s.label] = s.attribute;
  const specSwap: Record<string, { spec: string; attribute: string }> = {};
  for (const row of d.skill_attribute_swaps || []) {
    if (row.spec) specSwap[row.skill] = { spec: row.spec, attribute: row.attribute };
    else skillAttr[row.skill] = row.attribute;
  }
  return { skillAttr, specSwap };
}

/**
 * A vehicle's Handling, split.
 *
 * Chummer prints it as the sheet does: one number for a drone (`"3"`) and
 * two for anything that leaves the road (`"2/1"`, on-road then off-road). A
 * rating modifier can leave either side non-numeric, and then it is dropped
 * rather than guessed at.
 */
export function vehicleHandling(handling: string): { onroad: number; offroad: number | null } {
  const [on, off] = String(handling ?? "")
    .split("/")
    .map((part) => Number.parseInt(part.trim(), 10));
  return {
    onroad: Number.isFinite(on) ? on : 0,
    offroad: Number.isFinite(off) ? off : null,
  };
}

/** A vehicle's or drone's physical condition monitor: 12 + half its Body,
 *  rounded up (SR5 p.199). A microdrone has Body 0 and still has 12 boxes. */
export function vehicleConditionMonitor(body: string | number): number {
  const n = Number.parseInt(String(body ?? ""), 10);
  return 12 + Math.ceil(Math.max(Number.isFinite(n) ? n : 0, 0) / 2);
}

/**
 * The skills that drive, fly and shoot from a vehicle.
 *
 * Taken from the catalog by category rather than by name: which Pilot skills
 * exist depends on the books turned on (`Pilot Aerospace` is one of them).
 * Gunnery is the one that is not a Pilot skill, so it is named.
 */
export function vehicleSkills(catalog: Catalog): { pilots: string[]; gunnery: string } {
  const rows = (catalog.skills?.skills || []).filter((s) => s.category === "Vehicle Active");
  return {
    pilots: rows.filter((s) => s.name !== "Gunnery").map((s) => s.name),
    gunnery: rows.some((s) => s.name === "Gunnery") ? "Gunnery" : "",
  };
}
