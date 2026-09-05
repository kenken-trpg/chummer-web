import type { PriorityCategory, PriorityLetter } from "@/lib/types";
import type { MsgKey, UiFn } from "@/lib/i18n";

/** Look a code up in a key table, falling back to the code itself. */
function labeller(table: Record<string, MsgKey>) {
  return (code: string, ui: UiFn): string => (table[code] ? ui(table[code]) : code);
}

export const CATS: { key: PriorityCategory; label: MsgKey }[] = [
  { key: "Heritage", label: "prio.cat.heritage" },
  { key: "Attributes", label: "prio.cat.attributes" },
  { key: "Talent", label: "prio.cat.talent" },
  { key: "Skills", label: "prio.cat.skills" },
  { key: "Resources", label: "prio.cat.resources" },
];
export const LETTERS: PriorityLetter[] = ["A", "B", "C", "D", "E"];
export const SUM_TO_TEN_COST: Record<PriorityLetter, number> = { A: 4, B: 3, C: 2, D: 1, E: 0 };
export const DEFAULT_PRIORITIES: Record<PriorityCategory, PriorityLetter> = {
  Heritage: "C",
  Attributes: "A",
  Talent: "E",
  Skills: "B",
  Resources: "D",
};
export const ATTRS = [
  "BOD",
  "AGI",
  "REA",
  "STR",
  "WIL",
  "LOG",
  "INT",
  "CHA",
  "EDG",
  "MAG",
  "RES",
] as const;
// Attribute labels now come from the lang file via attrLabel()/attrShort()
// in @/lib/ui-strings (backed by ja-jp.xml + ja_overrides/ui.json).
export const KNOW_CATS = ["Academic", "Interest", "Language", "Professional", "Street"] as const;
const KNOW_CAT_KEYS: Record<string, MsgKey> = {
  Academic: "sr.know.academic",
  Interest: "sr.know.interest",
  Language: "sr.know.language",
  Professional: "sr.know.professional",
  Street: "sr.know.street",
};
export const knowCatLabel = labeller(KNOW_CAT_KEYS);

/**
 * SR5 p.130 groups the active skills into these categories and prints them in
 * this order; the official sheet and Chummer5a's category sort agree. The
 * catalog ships the same list (`skills.active_categories`, straight out of the
 * vendored `<categories>` block) — this is the fallback for a catalog that
 * predates that field, and the source of the Japanese headings either way.
 */
export const ACTIVE_SKILL_CATS = [
  "Combat Active",
  "Physical Active",
  "Social Active",
  "Magical Active",
  "Pseudo-Magical Active",
  "Resonance Active",
  "Technical Active",
  "Vehicle Active",
] as const;
const ACTIVE_SKILL_CAT_KEYS: Record<string, MsgKey> = {
  "Combat Active": "sr.skillcat.combat",
  "Physical Active": "sr.skillcat.physical",
  "Social Active": "sr.skillcat.social",
  "Magical Active": "sr.skillcat.magical",
  "Pseudo-Magical Active": "sr.skillcat.pseudomagical",
  "Resonance Active": "sr.skillcat.resonance",
  "Technical Active": "sr.skillcat.technical",
  "Vehicle Active": "sr.skillcat.vehicle",
};
export const skillCatLabel = labeller(ACTIVE_SKILL_CAT_KEYS);

export const CONTACT_ROLES = [
  "Fixer",
  "Street Doc",
  "Talismonger",
  "Mechanic",
  "Fence",
  "Mr. Johnson",
  "Bartender",
  "Cop",
  "Deckmeister",
];
export const MATRIX_ATTRS = [
  ["attack", "ATK"],
  ["sleaze", "SLZ"],
  ["dataprocessing", "DP"],
  ["firewall", "FW"],
] as const;
export const DEFAULT_ARRAY_ORDER = ["attack", "sleaze", "dataprocessing", "firewall"];

export type Tab =
  | "priority"
  | "meta"
  | "attrs"
  | "skills"
  | "qualities"
  | "cyber"
  | "bio"
  | "gear"
  | "contacts"
  | "martial"
  | "initiation"
  | "submersion"
  | "adept"
  | "spells"
  | "spirits"
  | "foci"
  | "complexforms"
  | "sprites"
  | "check"
  | "sheet";
export type GearKind =
  | "armor"
  | "weapon"
  | "commlink"
  | "cyberdeck"
  | "rcc"
  | "optics"
  | "sensor"
  | "drone"
  | "vehicle"
  | "misc"
  | "drugs"
  | "lifestyle";
export const OPTICS_DEVICE_CATS = new Set(["Vision Devices", "Audio Devices"]);
export const SENSOR_DEVICE_CATS = new Set(["Sensors", "Sensor Housings"]);
export const VEHICLE_INTERIOR_CATS = new Set([
  "Commlink Accessories",
  "Electronics Accessories",
  "Communications and Countermeasures",
]);
const R5_SLOT_KEYS: Record<string, MsgKey> = {
  Powertrain: "sr.r5.powertrain",
  Protection: "sr.r5.protection",
  Weapons: "sr.r5.weapons",
  Body: "sr.r5.body",
  Electromagnetic: "sr.r5.electromagnetic",
  Cosmetic: "sr.r5.cosmetic",
};
export const r5SlotLabel = (code: string, ui: UiFn): string | null =>
  R5_SLOT_KEYS[code] ? ui(R5_SLOT_KEYS[code]) : null;

export const CORE_LIFESTYLES = new Set(["Street", "Squatter", "Low", "Medium", "High", "Luxury"]);

const SPIRIT_ROLE_KEYS: Record<string, MsgKey> = {
  combat: "sr.spirit.combat",
  detection: "sr.spirit.detection",
  health: "sr.spirit.health",
  illusion: "sr.spirit.illusion",
  manipulation: "sr.spirit.manipulation",
  extra: "sr.spirit.extra",
};
export const spiritRoleLabel = labeller(SPIRIT_ROLE_KEYS);

const SIDE_KEYS: Record<string, MsgKey> = { Left: "common.left", Right: "common.right" };
export const sideLabel = labeller(SIDE_KEYS);

const REDLINER_SLOT_KEYS: Record<string, MsgKey> = {
  arm: "sr.limb.arm",
  leg: "sr.limb.leg",
  torso: "sr.limb.torso",
  skull: "sr.limb.skull",
};
export const redlinerSlotLabel = labeller(REDLINER_SLOT_KEYS);
