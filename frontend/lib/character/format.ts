import type { Character, LimitModifier, MagicTestInfo, SpecialArmor } from "@/lib/types";
import { ATTRS, REDLINER_SLOT_JA } from "@/lib/character/constants";

export function formatPoints(value: number) {
  const rounded = Math.round(value * 100) / 100;
  return String(rounded);
}

export function kindLabel(kind?: string) {
  if (kind === "ritual") return "儀式";
  if (kind === "enchantment") return "エンチャント";
  return "呪文";
}

export function optionalNumber(value: string): number | null {
  if (value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function testLine(test?: MagicTestInfo | null, drainLabel = "ドレイン") {
  if (!test) return "";
  const drain = test.drain == null ? `2×相手ヒット（最低2）` : `${test.drain}${test.drain_code || ""}`;
  const net = test.net == null ? "" : ` ・ 正味 ${test.net}`;
  const miss = test.missing ? " ・ 技能なし" : "";
  const days = test.days ? ` ・ ${test.days}日` : "";
  const vs = test.vs ? ` vs ${test.vs}` : "";
  return `${test.skill} ${test.pool} [${test.limit}]${vs} → ${drainLabel} ${drain}${net}${days}${miss}`;
}

export function cfDuration(value?: string) {
  if (value === "P") return "永続";
  if (value === "S") return "維持";
  if (value === "I") return "瞬間";
  if (value === "E") return "永続";
  return value || "";
}

export function lifeIncrement(inc?: string) {
  return inc === "day" ? "日" : "ヶ月";
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

export function formatAmmoCost(cost: string, costfor?: number) {
  const numeric = Number(cost);
  const yen = Number.isFinite(numeric) ? `${numeric.toLocaleString()}¥` : `${cost}¥`;
  if (costfor && costfor > 1) return `${yen} / ${costfor}発`;
  return yen;
}
export function specialArmorBits(sa?: SpecialArmor | null): { label: string; value: string }[] {
  if (!sa) return [];
  const rows: { label: string; value: string }[] = [];
  if (sa.fire) rows.push({ label: "耐火", value: `+${sa.fire}` });
  if (sa.cold) rows.push({ label: "断熱", value: `+${sa.cold}` });
  if (sa.electricity) rows.push({ label: "絶縁", value: `+${sa.electricity}` });
  if (sa.radiation) rows.push({ label: "放射線", value: `+${sa.radiation}` });
  const toxinContact = sa.toxin_contact || 0;
  const toxinIngest = sa.toxin_ingestion || 0;
  const toxinInhale = sa.toxin_inhalation || 0;
  const toxinInject = sa.toxin_injection || 0;
  const pathogenContact = sa.pathogen_contact || 0;
  const pathogenIngest = sa.pathogen_ingestion || 0;
  const pathogenInhale = sa.pathogen_inhalation || 0;
  const pathogenInject = sa.pathogen_injection || 0;
  if (toxinContact && toxinContact === pathogenContact) rows.push({ label: "化学防護(接触)", value: `+${toxinContact}` });
  else {
    if (toxinContact) rows.push({ label: "毒素接触", value: `+${toxinContact}` });
    if (pathogenContact) rows.push({ label: "病原接触", value: `+${pathogenContact}` });
  }
  if (toxinInhale && toxinInhale === pathogenInhale) rows.push({ label: "化学防護(吸入)", value: `+${toxinInhale}` });
  else {
    if (toxinInhale) rows.push({ label: "毒素吸入", value: `+${toxinInhale}` });
    if (pathogenInhale) rows.push({ label: "病原吸入", value: `+${pathogenInhale}` });
  }
  if (toxinIngest && toxinIngest === pathogenIngest) rows.push({ label: "化学防護(摂取)", value: `+${toxinIngest}` });
  else {
    if (toxinIngest) rows.push({ label: "毒素摂取", value: `+${toxinIngest}` });
    if (pathogenIngest) rows.push({ label: "病原摂取", value: `+${pathogenIngest}` });
  }
  if (toxinInject && toxinInject === pathogenInject) rows.push({ label: "化学防護(注射)", value: `+${toxinInject}` });
  else {
    if (toxinInject) rows.push({ label: "毒素注射", value: `+${toxinInject}` });
    if (pathogenInject) rows.push({ label: "病原注射", value: `+${pathogenInject}` });
  }
  const immunities = sa.immunities || {};
  const contact = Boolean(immunities.toxin_contact && immunities.pathogen_contact);
  const inhale = Boolean(immunities.toxin_inhalation && immunities.pathogen_inhalation);
  if (contact && inhale) rows.push({ label: "化学密閉", value: "免疫" });
  else {
    if (contact) rows.push({ label: "接触免疫", value: "免疫" });
    if (inhale) rows.push({ label: "吸入免疫", value: "免疫" });
  }
  return rows;
}

export function specialArmorLine(sa?: SpecialArmor | null): string {
  return specialArmorBits(sa)
    .map((row) => (row.value === "免疫" ? row.label : `${row.label} ${row.value}`))
    .join(" / ");
}

export function limitModifierLine(mods?: LimitModifier[] | null): string {
  if (!mods?.length) return "";
  const names: Record<string, string> = { physical: "物理", mental: "精神", social: "社会" };
  return mods.map((mod) => {
    const sign = mod.value > 0 ? `+${mod.value}` : `${mod.value}`;
    const base = `${names[mod.limit] || mod.limit}リミット ${sign}`;
    return mod.condition_label ? `${base}（${mod.condition_label}）` : base;
  }).join(" / ");
}

export function deviceRatingBit(item?: { device_rating?: number } | null): string {
  if (!item || !(item.device_rating || 0)) return "";
  return ` / DR ${item.device_rating}`;
}

export function wareAttrLine(bonus?: Record<string, number> | null): string {
  return ATTRS
    .filter((key) => (bonus?.[key] || 0) !== 0)
    .map((key) => `${key} +${bonus![key]}`)
    .join(" / ");
}

export function availBit(item?: { avail?: string; avail_value?: number } | null): string {
  if (!item) return "";
  if ((item.avail_value || 0) <= 0 && (!item.avail || item.avail === "0")) return "";
  if (!item.avail) return "";
  return ` / 入手 ${item.avail}`;
}

export function mergeSpecialArmor(mods?: { special_armor?: SpecialArmor }[]): SpecialArmor | undefined {
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
      toxin_inhalation: Boolean(out.immunities?.toxin_inhalation || sa.immunities?.toxin_inhalation),
      pathogen_contact: Boolean(out.immunities?.pathogen_contact || sa.immunities?.pathogen_contact),
      pathogen_inhalation: Boolean(out.immunities?.pathogen_inhalation || sa.immunities?.pathogen_inhalation),
    };
  }
  return out;
}
export function skillDice(rating: number, bonus?: number) {
  if (!bonus) return String(rating);
  const sign = bonus > 0 ? "+" : "";
  return `${rating} ${sign}${bonus}`;
}

export function mergeRatings(base?: Record<string, number> | null, extra?: Record<string, number> | null) {
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

export function limbQualityLine(q: NonNullable<Character["derived"]["limb_quality"]>) {
  const bits: string[] = [];
  if (q.limb_bonus) bits.push(`肢 STR/AGI +${q.limb_bonus}`);
  for (const [key, value] of Object.entries(q.attribute_bonus || {})) {
    if (key === "STR" || key === "AGI" || !value) continue;
    bits.push(`${key} +${value}`);
  }
  if (q.cm_physical) bits.push(`物理CM ${q.cm_physical}`);
  const effect = bits.length ? bits.join(" ・ ") : "ボーナスなし";
  const parts = (q.include || ["arm", "leg"]).map((slot) => REDLINER_SLOT_JA[slot] || slot).join("・");
  return `リム本数 Quality ${q.count}本（${q.pairs}組 / ${parts}） ・ ${effect}`;
}
