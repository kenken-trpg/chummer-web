import type { Character, LimitModifier, MagicTestInfo, SpecialArmor } from "@/lib/types";
import { ATTRS, redlinerSlotLabel } from "@/lib/character/constants";
import type { MsgKey, UiFn } from "@/lib/i18n";

export function formatPoints(value: number) {
  const rounded = Math.round(value * 100) / 100;
  return String(rounded);
}

/** Leading (possibly negative) integer of a stat string like "12" or "H4/3". */
export function leadInt(v?: string | number | null) {
  const m = String(v ?? "").match(/-?\d+/);
  return m ? parseInt(m[0], 10) : 0;
}

/** Matrix condition monitor: 8 + ⌈Device Rating ÷ 2⌉ (SR5 p.229). */
export function matrixCM(deviceRating?: number) {
  return 8 + Math.ceil((deviceRating || 0) / 2);
}

/** Vehicle/drone physical condition monitor: 12 + ⌈Body ÷ 2⌉ (SR5 p.199). */
export function vehicleCM(body?: string | number) {
  return 12 + Math.ceil(leadInt(body) / 2);
}

export function kindLabel(kind: string | undefined, ui: UiFn) {
  if (kind === "ritual") return ui("sr.kind.ritual");
  if (kind === "enchantment") return ui("sr.kind.enchantment");
  return ui("sr.kind.spell");
}

export function optionalNumber(value: string): number | null {
  if (value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function testLine(
  test: MagicTestInfo | null | undefined,
  ui: UiFn,
  drainKey: MsgKey = "fmt.drain",
) {
  if (!test) return "";
  const drain =
    test.drain == null ? ui("fmt.drainOpposed") : `${test.drain}${test.drain_code || ""}`;
  const net = test.net == null ? "" : ui("fmt.net", { net: test.net });
  const miss = test.missing ? ui("fmt.noSkill") : "";
  const days = test.days ? ui("fmt.days", { days: test.days }) : "";
  const vs = test.vs ? ` vs ${test.vs}` : "";
  return `${test.skill} ${test.pool} [${test.limit}]${vs} → ${ui(drainKey)} ${drain}${net}${days}${miss}`;
}

export function cfDuration(value: string | undefined, ui: UiFn) {
  if (value === "P" || value === "E") return ui("sr.dur.permanent");
  if (value === "S") return ui("sr.dur.sustained");
  if (value === "I") return ui("sr.dur.instantCf");
  return value || "";
}

const CF_TARGET: Record<string, MsgKey> = {
  Persona: "sr.cf.persona",
  Device: "sr.cf.device",
  Host: "sr.cf.host",
  File: "sr.cf.file",
  Icon: "sr.cf.icon",
  Self: "sr.cf.self",
  Sprite: "sr.cf.sprite",
  Cyberware: "sr.cf.cyberware",
};

export function cfTarget(value: string | undefined, ui: UiFn) {
  const key = value ? CF_TARGET[value] : undefined;
  return key ? ui(key) : value || "";
}

export function lifeIncrement(inc: string | undefined, ui: UiFn) {
  return ui(inc === "day" ? "fmt.increment.day" : "fmt.increment.month");
}

export function formatAccessoryCost(cost: string, parentCost?: string) {
  const raw = String(cost || "0").trim();
  const parent = Number(parentCost || 0);
  if (raw === "Weapon Cost" || raw === "Armor Cost") {
    return `${parent.toLocaleString()}¥`;
  }
  const numeric = Number(raw);
  if (Number.isFinite(numeric)) return `${numeric.toLocaleString()}¥`;
  return `${raw}¥`;
}

export function formatAmmoCost(cost: string, costfor: number | undefined, ui: UiFn) {
  const numeric = Number(cost);
  const yen = Number.isFinite(numeric) ? `${numeric.toLocaleString()}¥` : `${cost}¥`;
  if (costfor && costfor > 1) return ui("fmt.perRounds", { yen, count: costfor });
  return yen;
}
export type ArmorBit = { label: string; value: string; immune?: boolean };

/** Elemental + chemical protection rows. A vector whose toxin and pathogen
 *  ratings match collapses into one "chemical (…)" row — the four vectors
 *  behave identically, so they are one loop rather than four copies. */
export function specialArmorBits(sa: SpecialArmor | null | undefined, ui: UiFn): ArmorBit[] {
  if (!sa) return [];
  const rows: ArmorBit[] = [];
  const elemental = ["fire", "cold", "electricity", "radiation"] as const;
  for (const el of elemental) {
    if (sa[el]) rows.push({ label: ui(`fmt.armor.${el}`), value: `+${sa[el]}` });
  }
  const vectors = ["contact", "inhalation", "ingestion", "injection"] as const;
  for (const v of vectors) {
    const toxin = sa[`toxin_${v}`] || 0;
    const pathogen = sa[`pathogen_${v}`] || 0;
    if (toxin && toxin === pathogen) {
      rows.push({ label: ui(`fmt.armor.chem.${v}`), value: `+${toxin}` });
      continue;
    }
    if (toxin) rows.push({ label: ui(`fmt.armor.toxin.${v}`), value: `+${toxin}` });
    if (pathogen) rows.push({ label: ui(`fmt.armor.pathogen.${v}`), value: `+${pathogen}` });
  }
  const immunities = sa.immunities || {};
  const contact = Boolean(immunities.toxin_contact && immunities.pathogen_contact);
  const inhale = Boolean(immunities.toxin_inhalation && immunities.pathogen_inhalation);
  const immune = ui("fmt.armor.immune");
  if (contact && inhale) rows.push({ label: ui("fmt.armor.sealed"), value: immune, immune: true });
  else {
    if (contact) rows.push({ label: ui("fmt.armor.immuneContact"), value: immune, immune: true });
    if (inhale) rows.push({ label: ui("fmt.armor.immuneInhalation"), value: immune, immune: true });
  }
  return rows;
}

export function specialArmorLine(sa: SpecialArmor | null | undefined, ui: UiFn): string {
  return specialArmorBits(sa, ui)
    .map((row) => (row.immune ? row.label : `${row.label} ${row.value}`))
    .join(" / ");
}

const LIMIT_KEYS: Record<string, MsgKey> = {
  physical: "fmt.limit.physical",
  mental: "fmt.limit.mental",
  social: "fmt.limit.social",
};

export function limitModifierLine(mods: LimitModifier[] | null | undefined, ui: UiFn): string {
  if (!mods?.length) return "";
  return mods
    .map((mod) => {
      const sign = mod.value > 0 ? `+${mod.value}` : `${mod.value}`;
      const key = LIMIT_KEYS[mod.limit];
      const base = ui("fmt.limit.line", { name: key ? ui(key) : mod.limit, sign });
      return mod.condition_label ? `${base}（${mod.condition_label}）` : base;
    })
    .join(" / ");
}

export function deviceRatingBit(item?: { device_rating?: number } | null): string {
  if (!item || !(item.device_rating || 0)) return "";
  return ` / DR ${item.device_rating}`;
}

export function wareAttrLine(bonus?: Record<string, number> | null): string {
  return ATTRS.filter((key) => (bonus?.[key] || 0) !== 0)
    .map((key) => `${key} +${bonus![key]}`)
    .join(" / ");
}

export function availBit(
  item: { avail?: string; avail_value?: number } | null | undefined,
  ui: UiFn,
): string {
  if (!item) return "";
  if ((item.avail_value || 0) <= 0 && (!item.avail || item.avail === "0")) return "";
  if (!item.avail) return "";
  return ui("fmt.avail", { avail: item.avail });
}

export function mergeSpecialArmor(
  mods?: { special_armor?: SpecialArmor }[],
): SpecialArmor | undefined {
  let out: SpecialArmor | undefined;
  for (const mod of mods || []) {
    const sa = mod.special_armor;
    if (!sa) continue;
    out = out || { immunities: {} };
    out.fire = (out.fire || 0) + (sa.fire || 0);
    out.cold = (out.cold || 0) + (sa.cold || 0);
    out.electricity = (out.electricity || 0) + (sa.electricity || 0);
    out.radiation = (out.radiation || 0) + (sa.radiation || 0);
    out.toxin_contact = (out.toxin_contact || 0) + (sa.toxin_contact || 0);
    out.pathogen_contact = (out.pathogen_contact || 0) + (sa.pathogen_contact || 0);
    out.immunities = {
      toxin_contact: Boolean(out.immunities?.toxin_contact || sa.immunities?.toxin_contact),
      toxin_inhalation: Boolean(
        out.immunities?.toxin_inhalation || sa.immunities?.toxin_inhalation,
      ),
      pathogen_contact: Boolean(
        out.immunities?.pathogen_contact || sa.immunities?.pathogen_contact,
      ),
      pathogen_inhalation: Boolean(
        out.immunities?.pathogen_inhalation || sa.immunities?.pathogen_inhalation,
      ),
    };
  }
  return out;
}
export function skillDice(rating: number, bonus?: number) {
  if (!bonus) return String(rating);
  const sign = bonus > 0 ? "+" : "";
  return `${rating} ${sign}${bonus}`;
}

export function mergeRatings(
  base?: Record<string, number> | null,
  extra?: Record<string, number> | null,
) {
  const out: Record<string, number> = { ...(base || {}) };
  for (const [name, rating] of Object.entries(extra || {})) {
    out[name] = Math.max(out[name] || 0, rating || 0);
  }
  return out;
}

export function poolRating(pool: Record<string, number>, name: string) {
  let best = pool[name] || 0;
  const prefix = `${name} (`;
  for (const [key, value] of Object.entries(pool)) {
    if (key.startsWith(prefix)) best = Math.max(best, value || 0);
  }
  return best;
}

export function limbQualityLine(q: NonNullable<Character["derived"]["limb_quality"]>, ui: UiFn) {
  const bits: string[] = [];
  if (q.limb_bonus) bits.push(ui("fmt.limb.bonus", { bonus: q.limb_bonus }));
  for (const [key, value] of Object.entries(q.attribute_bonus || {})) {
    if (key === "STR" || key === "AGI" || !value) continue;
    bits.push(`${key} +${value}`);
  }
  if (q.cm_physical) bits.push(ui("fmt.limb.cm", { cm: q.cm_physical }));
  const effect = bits.length ? bits.join(` ${ui("common.termSep")} `) : ui("fmt.limb.noBonus");
  const parts = (q.include || ["arm", "leg"])
    .map((slot) => redlinerSlotLabel(slot, ui))
    .join(ui("common.termSep"));
  return ui("fmt.limb.quality", { count: q.count, pairs: q.pairs, parts, effect });
}
