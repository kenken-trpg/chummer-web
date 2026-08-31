import type { SpecialArmor, WeaponRangeBands } from "@/lib/types";

// Weapon categories in weapons.xml with no direct entry in ranges.xml.
const RANGE_CAT_ALIAS: Record<string, string> = {
  "Heavy Machine Guns": "Medium/Heavy Machinegun",
  "Medium Machine Guns": "Medium/Heavy Machinegun",
};

/** ranges.xml range name for a weapon: explicit <range>, else category. */
export function rangeNameFor(w: { range?: string; category?: string }) {
  return (w.range || "").trim() || RANGE_CAT_ALIAS[w.category || ""] || w.category || "";
}

/** Evaluate a ranges.xml band formula ("5", "{STR}*10", "{STR}/2", "-1"). */
function evalRangeBand(formula: string | undefined, str: number): number | null {
  const f = (formula || "").trim();
  if (!f || f === "-1") return null;
  const m = f
    .replace(/\{STR\}/gi, String(str))
    .match(/^(\d+(?:\.\d+)?)(?:\s*([*/])\s*(\d+(?:\.\d+)?))?$/);
  if (!m) return null;
  let v = parseFloat(m[1]);
  if (m[2] === "*") v *= parseFloat(m[3]);
  else if (m[2] === "/") v /= parseFloat(m[3]);
  return Math.floor(v);
}

/** The four "min–max metre" band strings for a resolved range table entry. */
export function rangeRow(bands: WeaponRangeBands, str: number): string[] {
  const nums = [bands.short, bands.medium, bands.long, bands.extreme].map((b) =>
    evalRangeBand(b, str),
  );
  const lows = [evalRangeBand(bands.min, str) ?? 0, nums[0], nums[1], nums[2]];
  return nums.map((hi, i) => {
    if (hi == null) return "–";
    const lo = (lows[i] ?? 0) + (i === 0 ? 0 : 1);
    return `${lo}–${hi}`;
  });
}

export function lifeIncrement(inc?: string) {
  return inc === "day" ? "日" : "ヶ月";
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
  if (toxinContact && toxinContact === pathogenContact)
    rows.push({ label: "化学防護(接触)", value: `+${toxinContact}` });
  else {
    if (toxinContact) rows.push({ label: "毒素接触", value: `+${toxinContact}` });
    if (pathogenContact) rows.push({ label: "病原接触", value: `+${pathogenContact}` });
  }
  if (toxinInhale) rows.push({ label: "毒素吸入", value: `+${toxinInhale}` });
  if (pathogenInhale) rows.push({ label: "病原吸入", value: `+${pathogenInhale}` });
  if (toxinIngest) rows.push({ label: "毒素摂取", value: `+${toxinIngest}` });
  if (pathogenIngest) rows.push({ label: "病原摂取", value: `+${pathogenIngest}` });
  if (toxinInject) rows.push({ label: "毒素注射", value: `+${toxinInject}` });
  if (pathogenInject) rows.push({ label: "病原注射", value: `+${pathogenInject}` });
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
