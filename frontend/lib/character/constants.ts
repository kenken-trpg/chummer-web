import type { PriorityCategory, PriorityLetter } from "@/lib/types";

export const CATS: { key: PriorityCategory; label: string }[] = [
  { key: "Heritage", label: "メタタイプ" },
  { key: "Attributes", label: "属性" },
  { key: "Talent", label: "魔法/レゾナンス" },
  { key: "Skills", label: "スキル" },
  { key: "Resources", label: "資金" },
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
export const ATTRS = ["BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA", "EDG", "MAG", "RES"] as const;
// Attribute labels now come from the lang file via attrLabel()/attrShort()
// in @/lib/ui-strings (backed by ja-jp.xml + ja_overrides/ui.json).
export const KNOW_CATS = ["Academic", "Interest", "Language", "Professional", "Street"] as const;
export const KNOW_CAT_JA: Record<string, string> = {
  Academic: "学術",
  Interest: "趣味",
  Language: "言語",
  Professional: "職業",
  Street: "街",
};

export const CONTACT_ROLES = ["Fixer", "Street Doc", "Talismonger", "Mechanic", "Fence", "Mr. Johnson", "Bartender", "Cop", "Deckmeister"];
export const MATRIX_ATTRS = [
  ["attack", "ATK"],
  ["sleaze", "SLZ"],
  ["dataprocessing", "DP"],
  ["firewall", "FW"],
] as const;
export const DEFAULT_ARRAY_ORDER = ["attack", "sleaze", "dataprocessing", "firewall"];

export type Tab = "priority" | "meta" | "attrs" | "skills" | "qualities" | "cyber" | "bio" | "gear" | "contacts" | "martial" | "initiation" | "submersion" | "adept" | "spells" | "spirits" | "foci" | "complexforms" | "sprites" | "sheet";
export type GearKind = "armor" | "weapon" | "commlink" | "cyberdeck" | "rcc" | "optics" | "sensor" | "drone" | "vehicle" | "misc" | "drugs" | "lifestyle";
export const OPTICS_DEVICE_CATS = new Set(["Vision Devices", "Audio Devices"]);
export const SENSOR_DEVICE_CATS = new Set(["Sensors", "Sensor Housings"]);
export const VEHICLE_INTERIOR_CATS = new Set([
  "Commlink Accessories",
  "Electronics Accessories",
  "Communications and Countermeasures",
]);
export const R5_SLOT_LABELS: Record<string, string> = {
  Powertrain: "パワートレイン",
  Protection: "防護",
  Weapons: "武器",
  Body: "ボディ",
  Electromagnetic: "電磁",
  Cosmetic: "外装",
};

export const CORE_LIFESTYLES = new Set(["Street", "Squatter", "Low", "Medium", "High", "Luxury"]);

export const SPIRIT_ROLE_JA: Record<string, string> = {
  combat: "戦闘",
  detection: "探知",
  health: "健康",
  illusion: "幻影",
  manipulation: "操作",
  extra: "追加",
};

export const SIDE_JA: Record<string, string> = { Left: "左", Right: "右" };

export const REDLINER_SLOT_JA: Record<string, string> = { arm: "腕", leg: "脚", torso: "胴", skull: "頭蓋" };

