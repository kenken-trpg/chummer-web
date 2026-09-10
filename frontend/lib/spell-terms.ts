// SR5 spell metadata → a display term. Fixed vocabularies from the rulebook,
// so a static map is enough (no lang-file round-trip) — but the map holds
// message keys rather than one language's words, and the caller supplies `ui`.
// A code the rulebook does not define passes through unchanged.

import type { MsgKey, UiFn } from "@/lib/i18n";

const SPELL_TYPE: Record<string, MsgKey> = {
  M: "sr.type.mana",
  P: "sr.type.physical",
};

const SPELL_RANGE: Record<string, MsgKey> = {
  T: "sr.range.touch",
  "T (A)": "sr.range.touchArea",
  LOS: "sr.range.los",
  "LOS (A)": "sr.range.losArea",
  S: "sr.range.self",
  "S (A)": "sr.range.selfArea",
  Special: "sr.range.special",
};

const SPELL_DURATION: Record<string, MsgKey> = {
  I: "sr.dur.instant",
  P: "sr.dur.permanent",
  S: "sr.dur.sustained",
  Special: "sr.dur.special",
};

/** Critter powers write their range and duration out in words where a spell
 *  uses a one-letter code, and add an action and an "Always" duration of their
 *  own (SR5 p.394). Anything else — `MAG x 50`, `F x 10 Combat Turns` — is a
 *  formula the table spells out, and passes through. */
const CRITTER_RANGE: Record<string, MsgKey> = {
  Self: "sr.range.self",
  Touch: "sr.range.touch",
  LOS: "sr.range.los",
  "LOS (A)": "sr.range.losArea",
  Special: "sr.range.special",
};

const CRITTER_DURATION: Record<string, MsgKey> = {
  Always: "sr.dur.always",
  Sustained: "sr.dur.sustained",
  Instant: "sr.dur.instant",
  Permanent: "sr.dur.permanent",
  Special: "sr.dur.special",
};

const CRITTER_ACTION: Record<string, MsgKey> = {
  Auto: "sr.action.auto",
  Free: "sr.action.free",
  Simple: "sr.action.simple",
  Complex: "sr.action.complex",
  Special: "sr.action.special",
  None: "sr.action.none",
};

const SPELL_DESCRIPTOR: Record<string, MsgKey> = {
  Area: "sr.desc.area",
  "Extended Area": "sr.desc.extendedArea",
  Direct: "sr.desc.direct",
  Indirect: "sr.desc.indirect",
  Elemental: "sr.desc.elemental",
  Mana: "sr.desc.mana",
  Physical: "sr.desc.physical",
  Realistic: "sr.desc.realistic",
  Active: "sr.desc.active",
  Passive: "sr.desc.passive",
  Essence: "sr.desc.essence",
  Environmental: "sr.desc.environmental",
  "Multi-Sense": "sr.desc.multiSense",
  "Single-Sense": "sr.desc.singleSense",
  Directional: "sr.desc.directional",
  Anchored: "sr.desc.anchored",
  Blood: "sr.desc.blood",
  Mental: "sr.desc.mental",
  Psychic: "sr.desc.psychic",
  "Material Link": "sr.desc.materialLink",
  "Organic Link": "sr.desc.organicLink",
  Minion: "sr.desc.minion",
  Spotter: "sr.desc.spotter",
  Spell: "sr.desc.spell",
  Contractual: "sr.desc.contractual",
  Adept: "sr.desc.adept",
  Negative: "sr.desc.negative",
  Obvious: "sr.desc.obvious",
  Damaging: "sr.desc.damaging",
  Geomancy: "sr.desc.geomancy",
  Object: "sr.desc.object",
};

const lookup =
  (table: Record<string, MsgKey>) =>
  (v: string | null | undefined, ui: UiFn): string => {
    const key = v ? table[v] : undefined;
    return key ? ui(key) : v || "";
  };

export const spellType = lookup(SPELL_TYPE);
export const spellRange = lookup(SPELL_RANGE);
export const spellDuration = lookup(SPELL_DURATION);
export const critterRange = lookup(CRITTER_RANGE);
export const critterDuration = lookup(CRITTER_DURATION);
export const critterAction = lookup(CRITTER_ACTION);

/** "物理 ・ 複雑 ・ 自身 ・ 維持" — what a spirit's power costs and how long it
 *  lasts, in the order the table prints it. Empty fields drop out: a few
 *  powers in the data give no action or no duration at all. */
export const critterPowerLine = (
  power: { type?: string; action?: string; range?: string; duration?: string },
  ui: UiFn,
): string =>
  [
    spellType(power.type, ui),
    critterAction(power.action, ui),
    critterRange(power.range, ui),
    critterDuration(power.duration, ui),
  ]
    .filter(Boolean)
    .join(ui("common.termSep"));

/** One line for a spirit's power: the translated name, and the table's terms
 *  in brackets. A power the data leaves blank prints as the name alone. */
export const critterPowerRow = (
  power: { name: string; type?: string; action?: string; range?: string; duration?: string },
  tr: (name: string) => string,
  ui: UiFn,
): string => {
  const detail = critterPowerLine(power, ui);
  const name = tr(power.name);
  return detail ? ui("common.powerRow", { name, detail }) : name;
};

/** "Indirect, Elemental, Area" → "間接・元素・効果範囲" / "Indirect · Elemental · Area" */
export const spellDescriptors = (v: string | null | undefined, ui: UiFn): string =>
  (v || "")
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean)
    .map((t) => (SPELL_DESCRIPTOR[t] ? ui(SPELL_DESCRIPTOR[t]) : t))
    .join(ui("common.termSep"));
