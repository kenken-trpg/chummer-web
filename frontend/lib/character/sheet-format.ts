import type { WeaponRangeBands } from "@/lib/types";

// Weapon categories in weapons.xml with no direct entry in ranges.xml.
const RANGE_CAT_ALIAS: Record<string, string> = {
  "Heavy Machine Guns": "Medium/Heavy Machinegun",
  "Medium Machine Guns": "Medium/Heavy Machinegun",
};

/** ranges.xml range name for a weapon: explicit <range>, else category. */
export function rangeNameFor(w: { range?: string; category?: string }) {
  return (w.range || "").trim() || RANGE_CAT_ALIAS[w.category || ""] || w.category || "";
}

/** Resolve `{STR}` in a weapon DV formula ("({STR}+1)P" -> "3P", "({STR})P" -> "2P").
 * Non-`{STR}` damage codes pass through untouched. */
export function resolveDamageStr(dv: string | undefined, str: number): string {
  const raw = (dv || "").trim();
  if (!/\{STR\}/i.test(raw)) return raw;
  return raw
    .replace(/\{STR\}\s*([+-]\s*\d+)?/gi, (_m, add?: string) =>
      String(str + (add ? parseInt(add.replace(/\s+/g, ""), 10) : 0)),
    )
    .replace(/\((-?\d+)\)/g, "$1"); // (3)P -> 3P
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
