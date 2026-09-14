"use client";
import type { TabPanelProps } from "@/components/character/types";
import type { Character } from "@/lib/types";

/** Which lists the Black Market Pipeline's category covers — the front end's
 *  half of the engine's `BLACK_MARKET_CATEGORY_HINTS`. */
const BLACK_MARKET_LISTS: Record<string, readonly (keyof Character & string)[]> = {
  Weapons: ["weapons"],
  Armor: ["armor"],
  Electronics: ["commlinks", "cyberdecks", "rccs", "optics", "sensors", "programs", "apps"],
  Vehicles: ["vehicles", "drones"],
  Cyberware: ["cyberware"],
  Bioware: ["bioware"],
  Drugs: ["gear"],
};

/**
 * "Bought black market": 10% off this one item (Chummer's `<discountedcost>`).
 *
 * The Black Market Pipeline is not a blanket discount — it lets the buyer
 * take 10% off items of its own category, one at a time — so this shows only
 * on a character who has it, and only in the lists that category covers.
 */
export function DiscountToggle({
  list,
  id,
  ch,
  d,
  ui,
  patch,
}: {
  /** the character list the row lives in, e.g. "weapons" */
  list: keyof Character & string;
  id: string;
  ch: Character;
  d: Character["derived"];
  ui: TabPanelProps["ui"];
  patch: TabPanelProps["patch"];
}) {
  const category = d.black_market_category || "";
  if (!d.black_market_discount || !(BLACK_MARKET_LISTS[category] || []).includes(list)) return null;
  const rows = (ch[list] || []) as { id?: string; discounted?: boolean }[];
  const row = rows.find((item) => item.id === id);
  if (!row) return null;
  return (
    <label title={ui("gear.blackMarketHint")}>
      <input
        type="checkbox"
        checked={!!row.discounted}
        onChange={(e) =>
          patch({
            [list]: rows.map((item) =>
              item.id === id ? { ...item, discounted: e.target.checked } : item,
            ),
          })
        }
      />
      {ui("gear.blackMarket")}
    </label>
  );
}
